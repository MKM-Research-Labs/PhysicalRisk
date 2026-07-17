// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

const CAPS = ["read", "write", "create", "delete"];
const $ = (id) => document.getElementById(id);

async function api(method, url, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const resp = await fetch(url, opts);
  let data = {};
  try { data = await resp.json(); } catch (e) { /* no body */ }
  return { ok: resp.ok, status: resp.status, data };
}

function show(el, visible) { el.classList.toggle("hidden", !visible); }
function msg(el, text, kind) { el.textContent = text || ""; el.className = "msg " + (kind || ""); }

let FUNCTIONS = [];

async function refresh() {
  const me = await api("GET", "/auth/me");
  if (!me.ok || !me.data.is_admin) {
    $("who").textContent = me.ok ? me.data.username + " (not an admin)" : "";
    show($("login-panel"), true);
    show($("add-panel"), false); show($("grid-panel"), false);
    show($("logout"), me.ok);
    if (me.ok && !me.data.is_admin) msg($("login-msg"), "This account is not an administrator.", "err");
    return;
  }
  $("who").textContent = "Signed in as " + me.data.username;
  show($("logout"), true);
  show($("login-panel"), false);
  show($("add-panel"), true); show($("grid-panel"), true);
  await loadGrid();
}

async function loadGrid() {
  const fns = await api("GET", "/admin/api/functions");
  const users = await api("GET", "/admin/api/users");
  if (!fns.ok || !users.ok) { msg($("grid-msg"), "Failed to load.", "err"); return; }
  FUNCTIONS = fns.data.functions;
  renderGrid(users.data.users);
}

function renderGrid(users) {
  const head = ["<tr><th class='user'>User</th>"];
  for (const f of FUNCTIONS) head.push(`<th colspan='4' title='${f.name}'>${f.code}</th>`);
  head.push("<th>Account</th></tr><tr><th class='user'></th>");
  for (const _ of FUNCTIONS) head.push("<th class='caps'>R</th><th class='caps'>W</th><th class='caps'>C</th><th class='caps'>D</th>");
  head.push("<th></th></tr>");

  const rows = [];
  for (const u of users) {
    const cells = [`<td class='user ${u.is_active ? "" : "inactive"}'>${u.username}</td>`];
    for (const f of FUNCTIONS) {
      const p = (u.permissions && u.permissions[f.code]) || {};
      for (const cap of CAPS) {
        const checked = p[cap] ? "checked" : "";
        cells.push(`<td><input type='checkbox' ${checked} data-user='${u.username}' data-func='${f.code}' data-cap='${cap}'></td>`);
      }
    }
    cells.push(`<td><button class='ghost' data-toggle='${u.username}' data-active='${u.is_active ? 1 : 0}'>${u.is_active ? "Disable" : "Enable"}</button> <button class='ghost' data-pw='${u.username}'>Password</button></td>`);
    rows.push("<tr>" + cells.join("") + "</tr>");
  }
  $("grid").innerHTML = "<table>" + head.join("") + rows.join("") + "</table>";

  $("grid").querySelectorAll("input[type=checkbox]").forEach((cb) =>
    cb.addEventListener("change", onPermChange));
  $("grid").querySelectorAll("button[data-toggle]").forEach((b) =>
    b.addEventListener("click", onToggleActive));
  $("grid").querySelectorAll("button[data-pw]").forEach((b) =>
    b.addEventListener("click", onSetPassword));
}

async function onPermChange(ev) {
  const cb = ev.target;
  const user = cb.dataset.user, func = cb.dataset.func;
  const flags = {};
  $("grid").querySelectorAll(`input[data-user='${user}'][data-func='${func}']`)
    .forEach((x) => { flags[x.dataset.cap] = x.checked; });
  const r = await api("POST", "/admin/api/permissions",
    Object.assign({ username: user, function_code: func }, flags));
  msg($("grid-msg"), r.ok ? `Saved ${user} · ${func}` : "Save failed", r.ok ? "ok" : "err");
}

async function onToggleActive(ev) {
  const user = ev.target.dataset.toggle;
  const makeActive = ev.target.dataset.active === "0";
  const r = await api("POST", `/admin/api/users/${user}/active`, { is_active: makeActive });
  if (r.ok) loadGrid(); else msg($("grid-msg"), "Update failed", "err");
}

async function onSetPassword(ev) {
  const user = ev.target.dataset.pw;
  const pw = window.prompt(`New password for ${user}:`);
  if (!pw) return;
  const r = await api("POST", `/admin/api/users/${user}/password`, { password: pw });
  msg($("grid-msg"), r.ok ? `Password set for ${user}` : "Failed", r.ok ? "ok" : "err");
}

async function doLogin() {
  const r = await api("POST", "/auth/login",
    { username: $("lg-user").value.trim(), password: $("lg-pass").value });
  if (r.ok) { $("lg-pass").value = ""; msg($("login-msg"), "", ""); refresh(); }
  else msg($("login-msg"), r.data.message || "Sign-in failed", "err");
}

async function doAddUser() {
  const r = await api("POST", "/admin/api/users", {
    username: $("nu-user").value.trim(), display_name: $("nu-name").value.trim(),
    password: $("nu-pass").value });
  if (r.ok) {
    $("nu-user").value = ""; $("nu-name").value = ""; $("nu-pass").value = "";
    msg($("add-msg"), "User created", "ok"); loadGrid();
  } else msg($("add-msg"), r.data.message || "Create failed", "err");
}

async function doLogout() { await api("POST", "/auth/logout"); refresh(); }

$("lg-go").addEventListener("click", doLogin);
$("lg-pass").addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });
$("nu-go").addEventListener("click", doAddUser);
$("logout").addEventListener("click", doLogout);
refresh();
