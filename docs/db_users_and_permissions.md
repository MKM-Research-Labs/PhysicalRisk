# Users & Permissions — simple Admin-managed RBAC

**Status:** Draft for review — 2026-06-18. Companion to
`docs/json_to_postgres_migration.md` (feeds WP5.1).

## The model in one sentence

An **Admin** creates users and, for each **function** (`Func001`, `Func002`, …), ticks
which of four boxes — **Read, Write, Create, Delete** — that user is allowed. Nobody but
an Admin can manage users or change permissions.

This replaces today's single shared password (`data/.port_admin`,
`routes/_admin_auth.py:require_admin_password`) which guards all ~65 mutating endpoints
with no notion of *who* is acting.

---

## 1. Capabilities (CRUD) — the only four

| Cap | Means |
|---|---|
| **Read** (R) | view / list / export |
| **Write** (W) | modify something that already exists |
| **Create** (C) | add a new record |
| **Delete** (D) | remove / void |

Simplifying rule: **any of W/C/D implies R.** You can't act on what you can't see.

---

## 2. Function registry — grows over the coming weeks

Each function has a **stable code** (`FuncNNN`) that never changes once issued, a display
name, and an `active` flag. The Admin screen renders one row per active function with four
checkboxes. Rolling out a new area = add a row here + tag its endpoints; no schema change.

### Live functions (today)

| Code | Name | Underlying actions / endpoints it gates |
|---|---|---|
| **Func001** | Create synthetic portfolio | the port generation pipeline (`python app.py port …` / its app-driven equivalent) — produces gauges/properties/loans/commercial/timeseries/curves |
| **Func002** | Upload real portfolio | ingest a real (customer) portfolio file → validate → load (the planned upload path; today partially in the CDM tool) |
| **Func003** | Trade PRS | trading desk — `prs/*` and `trading/*` (blotter, commit, close, EOD) |

### Reserved / coming (placeholders — fill in as you roll out)

| Code | Name (tentative) |
|---|---|
| Func004 | Run stress test |
| Func005 | Train classifiers |
| Func006 | Edit / review assets (CDM) |
| Func007 | Governance / MRC |
| Func008 | Risk analytics & reports |
| `Func000` | **Admin** — user & permission management (special, see §4) |

> The Func004+ names are guesses to show the shape — you'll confirm them when each rolls
> out. Only Func001–003 are real today.

### What R/W/C/D mean for each live function

| | Func001 — Create synthetic | Func002 — Upload real | Func003 — Trade PRS |
|---|---|---|---|
| **Read** | view synthetic portfolios / past generation runs | view uploaded real portfolios | view the blotter & trades |
| **Write** | re-run / change params of an existing synthetic portfolio | replace / correct an uploaded portfolio | amend / re-mark an open trade |
| **Create** | generate a **new** synthetic portfolio | upload a **new** real portfolio | commit a **new** PRS trade |
| **Delete** | delete a synthetic portfolio / run | remove an uploaded portfolio | close / void a trade |

---

## 3. Example grant matrix

Cells show the ticked boxes per function (`R W C D`; `—` = no access).

| User | Func001 (synthetic) | Func002 (upload) | Func003 (trade) | Func000 (admin) |
|---|---|---|---|---|
| `alice` (admin) | R W C D | R W C D | R W C D | **R W C D** |
| `bob` (trader) | R | R | R W C D | — |
| `carol` (data/quant) | R W C D | R W C D | R | — |
| `dave` (read-only) | R | R | R | — |

The `svc_app` login the web app connects with is **not** a person in this table — see §5.

---

## 4. The Admin (`Func000`)

- An Admin is any user with capability on `Func000`. Only they can: create / disable
  users, reset passwords, and tick/untick every other user's R/W/C/D per function
  (including granting `Func000` itself).
- Admins hold full capability on all functions by default.
- Every admin action (user created, checkbox changed) is written to the append-only
  `audit_log`, so permission changes are themselves auditable.

---

## 5. How it's stored & enforced (deliberately simple)

**Application-level RBAC, not Postgres GRANTs** — so the Admin manages it live through the
UI, no DBA. Tables owned by the single data-access utility `src/repository/` (per the
no-SQL-outside rule):

```
function(code PK 'Func001', name, description, is_active, sort_order)
app_user(id, username, display_name, is_active, password_hash | sso_subject, created_by)
permission(user_id, function_code FK, can_read, can_write, can_create, can_delete)
audit_log(id, actor_user_id, action, function_code, target, ts)   -- append-only
```

- A missing `permission` row = no access. Adding a function later inserts one `function`
  row; the Admin grid picks it up automatically.
- Enforcement is **one decorator**, calling the utility — no SQL in the route:

```python
@require("Func003", "create")     # 403 unless current user has Create on Func003
def commit_prs_trade(): ...

@require("Func001", "create")
def generate_synthetic_portfolio(): ...

@require_admin                    # = capability on Func000
def set_user_permissions(): ...
```

The web app still connects to Postgres as the single `svc_app` login; per-user CRUD is
checked in app logic via the repository, not via DB roles. Catchment scoping, if ever
needed, is a later extra column on `permission` — out of scope for "keep it simple" now.

---

## 6. Rollout (matches "over the next weeks")

1. Ship the tables + Admin screen with **Func001–Func003** active and `Func000` (admin).
2. Wire the decorator onto those functions' endpoints; retire `require_admin_password`
   and `data/.port_admin`.
3. Each following week: add a `function` row (Func004…), tag its endpoints, done — no
   migration, no redeploy of the permission model.

---

## 7. Open decisions for you

- **Confirm Func001–003 endpoint mapping** — especially Func002 (the "upload real
  portfolio" flow isn't fully built yet; where should it live?).
- **Identity source** — local DB users + passwords (+MFA), or wire to existing SSO/OIDC?
- **Bootstrap admin** — who is the first `Func000` user, and one admin or several?
- **Trade approval** — is `Create` on Func003 enough to commit, or do you want a separate
  maker/checker step (trader creates, risk/admin approves)?
