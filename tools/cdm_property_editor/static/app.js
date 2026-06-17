// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
// (see package __init__.py for full license text)
//
// Property CDM Review — front end.
//
// Follows the Model Governance workflow template: a left-hand list of all
// properties, each row carrying a right-hand "review" icon that opens the
// full CDM record in a centered modal with section tabs (governance detail
// style). Every tab's content is generated from the canonical CDM schema, so
// the UI stays in lock-step with the CDM definition.

let SCHEMA = null;        // { sections: [...], schema: {...} }
let PROPERTIES = [];      // menu summaries
let CURRENT = null;       // full record currently open in the modal
let CURRENT_ID = null;
let ACTIVE_SECTION = null;

const $ = (sel) => document.querySelector(sel);

const EYE_SVG =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
  'stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>' +
  '<circle cx="12" cy="12" r="3"/></svg>';

// ---- helpers ---------------------------------------------------------------

function isField(node) {
  return node && typeof node === "object" && !Array.isArray(node) &&
         typeof node.type === "string";
}

function prettyLabel(key) {
  return key
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2");
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function fmtMoney(v) {
  if (v === null || v === undefined) return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return "£" + n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function badge(text, cls) {
  return `<span class="badge ${cls || "badge-na"}">${text || "—"}</span>`;
}

function typeBadge(type) {
  const cls = { residential: "badge-residential", commercial: "badge-commercial",
                industrial: "badge-industrial" }[type] || "badge-na";
  return badge(type || "—", cls);
}

// ---- left list -------------------------------------------------------------

function renderMenu(filter = "") {
  const list = $("#property-list");
  const f = filter.trim().toLowerCase();
  const items = PROPERTIES.filter((p) =>
    !f ||
    (p.id && p.id.toLowerCase().includes(f)) ||
    (p.address && p.address.toLowerCase().includes(f)) ||
    (p.type && p.type.toLowerCase().includes(f))
  );

  list.innerHTML = "";
  for (const p of items) {
    const li = document.createElement("li");
    li.className = "property-item" + (p.id === CURRENT_ID ? " active" : "");
    li.dataset.id = p.id;
    li.innerHTML =
      `<div class="pi-main">` +
        `<div class="pi-id">${p.id}</div>` +
        `<div class="pi-addr">${p.address || ""}</div>` +
        `<div class="pi-meta">${typeBadge(p.type)}` +
          `<span class="pi-value">${fmtMoney(p.value)}</span></div>` +
      `</div>` +
      `<button class="review-btn" title="Review detailed data" ` +
        `aria-label="Review ${p.id}">${EYE_SVG}</button>`;
    // The review icon and the row both open the detail modal.
    li.querySelector(".review-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      openDetail(p.id);
    });
    li.addEventListener("click", () => openDetail(p.id));
    list.appendChild(li);
  }
  $("#count").textContent = `${items.length} / ${PROPERTIES.length} properties`;
}

// ---- summary dashboard -----------------------------------------------------

function renderSummary() {
  const cards = $("#cards");
  const n = PROPERTIES.length;
  const byType = {};
  let totalValue = 0;
  let active = 0;
  for (const p of PROPERTIES) {
    byType[p.type || "—"] = (byType[p.type || "—"] || 0) + 1;
    if (typeof p.value === "number") totalValue += p.value;
    if (p.status === "active") active += 1;
  }
  const typeLine = Object.entries(byType)
    .map(([k, v]) => `${k}: ${v}`).join(" · ");

  const card = (label, value, sub) =>
    `<div class="card"><div class="card-label">${label}</div>` +
    `<div class="card-value">${value}</div>` +
    (sub ? `<div class="card-sub">${sub}</div>` : "") + `</div>`;

  cards.innerHTML =
    card("Properties", n, typeLine) +
    card("Total Value", fmtMoney(totalValue), "portfolio market value") +
    card("Active", active, `${n - active} other`) +
    card("CDM Sections", (SCHEMA?.sections || []).length, "per property");
}

// ---- detail modal ----------------------------------------------------------

function renderDetailCard() {
  const h = CURRENT.PropertyHeader || {};
  const loc = h.Location || {};
  const val = h.Valuation || {};
  const hdr = h.Header || {};
  const addr = [loc.BuildingNumber, loc.StreetName, loc.TownCity, loc.Postcode]
    .filter(Boolean).join(" ");
  $("#detail-card").innerHTML =
    `<div class="dc-top">` +
      `<div>` +
        `<div class="dc-id">${CURRENT_ID}</div>` +
        `<div class="dc-sub">${addr || "(no address)"}` +
          (hdr.UPRN ? ` · UPRN ${hdr.UPRN}` : "") +
          (hdr.CatchmentID ? ` · ${hdr.CatchmentID}` : "") + `</div>` +
        `<div class="dc-badges">${typeBadge(hdr.propertyType)}` +
          `${badge(hdr.propertyStatus, "badge-status")}</div>` +
      `</div>` +
      `<div class="dc-value"><div class="label">Valuation</div>` +
        `<div class="amount">${fmtMoney(val.PropertyValue)}</div></div>` +
    `</div>`;
}

function renderDetailTabs() {
  const tabs = $("#detail-tabs");
  tabs.innerHTML = "";
  for (const section of SCHEMA.sections) {
    const btn = document.createElement("button");
    btn.className = "detail-tab" + (section === ACTIVE_SECTION ? " active" : "");
    btn.textContent = prettyLabel(section);
    btn.addEventListener("click", () => {
      ACTIVE_SECTION = section;
      renderDetailTabs();
      renderDetailBody();
    });
    tabs.appendChild(btn);
  }
}

// Ordered [key, node, value, kind] entries: schema-described first (schema
// order), then any data-only keys appended.
function orderedEntries(schema, data) {
  const out = [];
  const seen = new Set();
  for (const [key, node] of Object.entries(schema)) {
    seen.add(key);
    out.push([key, node, data[key], isField(node) ? "field" : "group"]);
  }
  for (const [key, val] of Object.entries(data)) {
    if (seen.has(key)) continue;
    const isObj = val && typeof val === "object" && !Array.isArray(val);
    out.push([key, isObj ? {} : null, val, isObj ? "group" : "field"]);
  }
  return out;
}

function renderField(key, descriptor, value) {
  const cell = document.createElement("div");
  cell.className = "field";

  const label = document.createElement("div");
  label.className = "field-label";
  label.textContent = prettyLabel(key);
  if (descriptor && descriptor.description) label.title = descriptor.description;

  const val = document.createElement("div");
  val.className = "field-value";
  val.textContent = formatValue(value);

  const typ = document.createElement("div");
  typ.className = "field-type";
  typ.textContent = descriptor ? descriptor.type : "unknown";

  cell.appendChild(label);
  cell.appendChild(val);
  cell.appendChild(typ);
  return cell;
}

// Single ordered pass: consecutive leaf fields collect into a grid; a
// sub-group flushes the grid and emits a sub-section block.
function renderGroup(schemaNode, dataNode, depth) {
  const frag = document.createDocumentFragment();
  const data = dataNode && typeof dataNode === "object" ? dataNode : {};
  const schema = schemaNode && typeof schemaNode === "object" ? schemaNode : {};

  let grid = null;
  const flush = () => { if (grid) { frag.appendChild(grid); grid = null; } };

  for (const [key, node, value, kind] of orderedEntries(schema, data)) {
    if (kind === "field") {
      if (!grid) { grid = document.createElement("div"); grid.className = "field-grid"; }
      grid.appendChild(renderField(key, node, value));
    } else {
      flush();
      const block = document.createElement("section");
      block.className = "subsection level-" + Math.min(depth, 3);
      const h = document.createElement("h3");
      h.className = "subsection-title";
      h.textContent = prettyLabel(key);
      block.appendChild(h);
      block.appendChild(renderGroup(node, value, depth + 1));
      frag.appendChild(block);
    }
  }
  flush();
  return frag;
}

function renderDetailBody() {
  const body = $("#detail-body");
  body.innerHTML = "";
  const schemaNode = SCHEMA.schema[ACTIVE_SECTION] || {};
  const dataNode = CURRENT[ACTIVE_SECTION] || {};
  body.appendChild(renderGroup(schemaNode, dataNode, 0));
  // Footer: a small field count for the active section.
  const count = body.querySelectorAll(".field").length;
  $("#modal-foot").innerHTML =
    `<span>Section: <b>${prettyLabel(ACTIVE_SECTION)}</b></span>` +
    `<span>${count} fields</span>`;
}

async function openDetail(pid) {
  setStatus("Loading " + pid + "…");
  try {
    const res = await fetch(`/api/properties/${encodeURIComponent(pid)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    CURRENT = await res.json();
    CURRENT_ID = pid;
    ACTIVE_SECTION = SCHEMA.sections[0];
    renderMenu($("#search").value);
    renderDetailCard();
    renderDetailTabs();
    renderDetailBody();
    $("#modal-overlay").classList.remove("hidden");
    setStatus("");
  } catch (err) {
    setStatus("Error: " + err.message, true);
  }
}

function closeModal() {
  $("#modal-overlay").classList.add("hidden");
}

function toggleExpand() {
  const m = $("#modal");
  const expanded = m.classList.toggle("expanded");
  const btn = $("#modal-expand");
  btn.innerHTML = expanded ? "&#x2750;" : "&#x26F6;";
  btn.title = expanded ? "Restore" : "Expand";
}

function setStatus(msg, isError = false) {
  const el = $("#status");
  el.textContent = msg;
  el.classList.toggle("error", isError);
}

// ---- boot ------------------------------------------------------------------

async function boot() {
  setStatus("Loading…");
  try {
    const [schemaRes, propsRes] = await Promise.all([
      fetch("/api/schema"),
      fetch("/api/properties"),
    ]);
    SCHEMA = await schemaRes.json();
    PROPERTIES = await propsRes.json();
    renderMenu();
    renderSummary();
    setStatus("");

    $("#search").addEventListener("input", (e) => renderMenu(e.target.value));
    $("#modal-close").addEventListener("click", closeModal);
    $("#modal-expand").addEventListener("click", toggleExpand);
    $("#modal-overlay").addEventListener("click", (e) => {
      if (e.target.id === "modal-overlay") closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });
  } catch (err) {
    setStatus("Failed to load: " + err.message, true);
  }
}

boot();
