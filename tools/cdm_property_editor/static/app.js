// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
// (see package __init__.py for full license text)
//
// CDM Asset Review — front end.
//
// Governance-workflow template: a top tab bar of asset classes (Gauges,
// Properties, Commercials, Mortgage, Commercial Loan), a left-hand list of
// every record in the active tab, each row carrying a right-hand review icon
// that opens the full CDM record in a centered modal with section tabs. All
// content is schema-driven from each asset's canonical CDM schema.

let ASSETS = [];          // [{key, label}]
let ASSET = null;         // active asset key
let SCHEMA = null;        // { sections: [...], schema: {...} } for active asset
let ITEMS = [];           // summary rows for active asset
let CURRENT = null;       // full record open in the modal
let CURRENT_ID = null;
let ACTIVE_SECTION = null;
let ACTIVE_PERIL = "flood";
let CURRENT_FLOODS = null; // floods payload for the open record (null = loading)

const PERILS = [
  { key: "flood", label: "Flood" },
  { key: "wind", label: "Wind" },
  { key: "fire", label: "Fire" },
  { key: "seismic", label: "Seismic" },
];

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
  return String(key)
    .replace(/^_/, "")
    .replace(/_/g, " ")
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
  if (v === null || v === undefined) return "";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return "£" + n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function badge(text, cls) {
  return `<span class="badge ${cls || "badge-na"}">${text || "—"}</span>`;
}

function assetLabel(key) {
  const a = ASSETS.find((x) => x.key === key);
  return a ? a.label : key;
}

// ---- top tab bar -----------------------------------------------------------

function renderAssetTabs() {
  const bar = $("#asset-tabs");
  bar.innerHTML = "";
  for (const a of ASSETS) {
    const btn = document.createElement("button");
    btn.className = "asset-tab" + (a.key === ASSET ? " active" : "");
    btn.textContent = a.label;
    btn.addEventListener("click", () => selectAsset(a.key));
    bar.appendChild(btn);
  }
}

// ---- left list -------------------------------------------------------------

function renderList(filter = "") {
  const list = $("#item-list");
  const f = filter.trim().toLowerCase();
  const items = ITEMS.filter((p) =>
    !f ||
    (p.id && String(p.id).toLowerCase().includes(f)) ||
    (p.sub && String(p.sub).toLowerCase().includes(f)) ||
    (p.tag && String(p.tag).toLowerCase().includes(f))
  );

  list.innerHTML = "";
  for (const p of items) {
    const li = document.createElement("li");
    li.className = "property-item" + (p.id === CURRENT_ID ? " active" : "");
    li.innerHTML =
      `<div class="pi-main">` +
        `<div class="pi-id">${p.id ?? "—"}</div>` +
        `<div class="pi-addr">${p.sub || ""}</div>` +
        `<div class="pi-meta">${badge(p.tag, p.tagClass)}` +
          `<span class="pi-value">${fmtMoney(p.value)}</span></div>` +
      `</div>` +
      `<button class="review-btn" title="Review detailed data" ` +
        `aria-label="Review ${p.id}">${EYE_SVG}</button>`;
    li.querySelector(".review-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      openDetail(p.id);
    });
    li.addEventListener("click", () => openDetail(p.id));
    list.appendChild(li);
  }
  $("#count").textContent = `${items.length} / ${ITEMS.length} ${assetLabel(ASSET).toLowerCase()}`;
}

// ---- summary dashboard -----------------------------------------------------

function renderSummary() {
  const cards = $("#cards");
  const n = ITEMS.length;
  const byTag = {};
  let totalValue = 0;
  let hasValue = false;
  for (const p of ITEMS) {
    const t = p.tag || "—";
    byTag[t] = (byTag[t] || 0) + 1;
    if (typeof p.value === "number") { totalValue += p.value; hasValue = true; }
  }
  const tagLine = Object.entries(byTag)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${k}: ${v}`).join(" · ");

  const card = (label, value, sub) =>
    `<div class="card"><div class="card-label">${label}</div>` +
    `<div class="card-value">${value}</div>` +
    (sub ? `<div class="card-sub">${sub}</div>` : "") + `</div>`;

  cards.innerHTML =
    card(assetLabel(ASSET), n, tagLine) +
    card("Total Value", hasValue ? fmtMoney(totalValue) : "—",
         hasValue ? "aggregate" : "no monetary value") +
    card("Categories", Object.keys(byTag).length, "distinct tags") +
    card("CDM Sections", (SCHEMA?.sections || []).length, "schema-defined");
}

// ---- detail modal ----------------------------------------------------------

// Mini location map: a self-rendered slippy map — OSM raster tiles placed as
// <img> elements with a centre marker. No library or API key; renders directly
// in our DOM (a cross-origin OSM iframe does not paint reliably here).
const MAP_W = 280, MAP_H = 110, MAP_Z = 15, TILE = 256;

function miniMapHtml(lat, lon) {
  if (typeof lat !== "number" || typeof lon !== "number") return "";
  const n = 2 ** MAP_Z;
  const xf = ((lon + 180) / 360) * n;
  const latRad = (lat * Math.PI) / 180;
  const yf = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n;
  const left = xf * TILE - MAP_W / 2; // world-pixel of the container's top-left
  const top = yf * TILE - MAP_H / 2;
  const x0 = Math.floor(left / TILE), x1 = Math.floor((left + MAP_W) / TILE);
  const y0 = Math.floor(top / TILE), y1 = Math.floor((top + MAP_H) / TILE);

  let tiles = "";
  for (let tx = x0; tx <= x1; tx++) {
    for (let ty = y0; ty <= y1; ty++) {
      if (tx < 0 || ty < 0 || tx >= n || ty >= n) continue;
      const px = tx * TILE - left, py = ty * TILE - top;
      tiles += `<img alt="" src="https://tile.openstreetmap.org/${MAP_Z}/${tx}/${ty}.png" ` +
        `style="left:${px}px;top:${py}px" />`;
    }
  }
  const big = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=${MAP_Z}/${lat}/${lon}`;
  return `<div class="dc-map">` +
    `<div class="mini-map">${tiles}<div class="map-pin"></div>` +
      `<span class="map-attr">© OpenStreetMap</span></div>` +
    `<div class="dc-coords">` +
      `<span>${lat.toFixed(5)}, ${lon.toFixed(5)}</span>` +
      `<a href="${big}" target="_blank" rel="noopener">Larger map ↗</a>` +
    `</div></div>`;
}

function renderDetailCard() {
  const s = ITEMS.find((x) => x.id === CURRENT_ID) || {};
  const valueHtml = (s.value === null || s.value === undefined)
    ? ""
    : `<div class="dc-value"><div class="label">Value</div>` +
      `<div class="amount">${fmtMoney(s.value)}</div></div>`;
  const hasMap = typeof s.lat === "number" && typeof s.lon === "number";

  // Right-hand aside (≤1/3): map + perils panel, sat inside the blue header
  // alongside the prop identity. Shown for assets that have a location.
  const aside = hasMap
    ? `<div class="dc-aside">` +
        `<div class="peril-card">` +
          `<div class="peril-tabs" id="peril-tabs"></div>` +
          `<div class="peril-content" id="peril-content"></div>` +
        `</div>` +
        miniMapHtml(s.lat, s.lon) +
      `</div>`
    : "";

  $("#detail-card").innerHTML =
    `<div class="dc-identity">` +
      `<div class="dc-info">` +
        `<div class="dc-id">${CURRENT_ID}</div>` +
        `<div class="dc-sub">${s.sub || ""}</div>` +
        `<div class="dc-badges">${badge(s.tag, s.tagClass)}` +
          `<span class="dc-asset">${assetLabel(ASSET)}</span></div>` +
        valueHtml +
      `</div>` + aside +
    `</div>`;
  if (hasMap) { renderPerilTabs(); renderPerilContent(); }
}

function renderPerilTabs() {
  const bar = $("#peril-tabs");
  if (!bar) return;
  bar.innerHTML = "";
  for (const p of PERILS) {
    const btn = document.createElement("button");
    btn.className = "peril-tab" + (p.key === ACTIVE_PERIL ? " active" : "");
    btn.textContent = p.label;
    if (p.key !== "flood") btn.classList.add("placeholder");
    btn.addEventListener("click", () => {
      ACTIVE_PERIL = p.key;
      renderPerilTabs();
      renderPerilContent();
    });
    bar.appendChild(btn);
  }
}

function clusterBadge(type) {
  const cls = { isolated: "cl-isolated", doublet: "cl-doublet",
                cluster: "cl-cluster", persistent: "cl-persistent" }[type] || "cl-na";
  return `<span class="cl-badge ${cls}">${type || "—"}</span>`;
}

function floodTableHtml() {
  if (CURRENT_FLOODS === null) return `<div class="peril-msg">Loading flood events…</div>`;
  if (!CURRENT_FLOODS.supported)
    return `<div class="peril-msg">Per-asset flood damage is not modelled for ${assetLabel(ASSET).toLowerCase()}.</div>`;
  const evs = CURRENT_FLOODS.events || [];
  if (!evs.length)
    return `<div class="peril-msg">No severe flood events on record` +
           (CURRENT_FLOODS.flood_zone ? ` &middot; ${CURRENT_FLOODS.flood_zone}` : "") + `.</div>`;

  let rows = "";
  for (const e of evs) {
    const tip = `peak ${e.peak_m} m · depth ${e.depth_m} m` +
                (e.intensity ? ` · ${e.intensity}` : "");
    rows +=
      `<tr title="${tip}">` +
        `<td class="pt-storm">${e.storm}</td>` +
        `<td>${clusterBadge(e.type)}</td>` +
        `<td class="pt-dmg">${e.damage_pct ? e.damage_pct.toFixed(1) + "%" : "—"}</td>` +
      `</tr>`;
  }
  const cap = `Top ${evs.length} of ${CURRENT_FLOODS.count} events` +
              (CURRENT_FLOODS.flood_zone ? ` &middot; ${CURRENT_FLOODS.flood_zone}` : "");
  return `<div class="peril-cap">${cap}</div>` +
    `<div class="peril-scroll"><table class="peril-table"><thead><tr>` +
      `<th>Storm</th><th>Type</th><th>Damage</th>` +
    `</tr></thead><tbody>${rows}</tbody></table></div>`;
}

function renderPerilContent() {
  const el = $("#peril-content");
  if (!el) return;
  if (ACTIVE_PERIL === "flood") { el.innerHTML = floodTableHtml(); return; }
  const label = (PERILS.find((p) => p.key === ACTIVE_PERIL) || {}).label || "";
  el.innerHTML =
    `<div class="peril-ph">` +
      `<div class="peril-ph-title">${label} perils</div>` +
      `<div class="peril-ph-sub">Coming soon — ${label.toLowerCase()} damage events ` +
        `will appear here.</div>` +
    `</div>`;
}

async function loadFloods() {
  if (!(ASSET && CURRENT_ID)) return;
  const reqId = CURRENT_ID;
  CURRENT_FLOODS = null;
  if (ACTIVE_PERIL === "flood") renderPerilContent();
  try {
    const res = await fetch(`/api/${ASSET}/items/${encodeURIComponent(CURRENT_ID)}/floods`);
    const data = await res.json();
    if (reqId !== CURRENT_ID) return; // a different record was opened meanwhile
    CURRENT_FLOODS = data;
  } catch (err) {
    if (reqId !== CURRENT_ID) return;
    CURRENT_FLOODS = { supported: false, events: [] };
  }
  if (ACTIVE_PERIL === "flood") renderPerilContent();
}

// Section tabs come from the record's own top-level keys, ordered schema-first
// then any data-only keys (e.g. _commercial_meta), so nothing is hidden.
function recordSections() {
  const schemaKeys = Object.keys(SCHEMA.schema);
  const dataKeys = Object.keys(CURRENT || {});
  const ordered = schemaKeys.filter((k) => dataKeys.includes(k));
  for (const k of dataKeys) if (!schemaKeys.includes(k)) ordered.push(k);
  return ordered.length ? ordered : dataKeys;
}

function renderDetailTabs() {
  const tabs = $("#detail-tabs");
  tabs.innerHTML = "";
  for (const section of recordSections()) {
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
  // A leaf-only section (rare) still renders by wrapping the value.
  if (dataNode && typeof dataNode === "object") {
    body.appendChild(renderGroup(schemaNode, dataNode, 0));
  } else {
    const grid = document.createElement("div");
    grid.className = "field-grid";
    grid.appendChild(renderField(ACTIVE_SECTION, isField(schemaNode) ? schemaNode : null, dataNode));
    body.appendChild(grid);
  }
  const count = body.querySelectorAll(".field").length;
  $("#modal-foot").innerHTML =
    `<span>Section: <b>${prettyLabel(ACTIVE_SECTION)}</b></span>` +
    `<span>${count} fields</span>`;
}

async function openDetail(rid) {
  setStatus("Loading " + rid + "…");
  try {
    const res = await fetch(`/api/${ASSET}/items/${encodeURIComponent(rid)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    CURRENT = await res.json();
    CURRENT_ID = rid;
    ACTIVE_SECTION = recordSections()[0];
    ACTIVE_PERIL = "flood";
    CURRENT_FLOODS = null;
    const singular = { Properties: "Property", Commercials: "Commercial",
                       Gauges: "Gauge" }[assetLabel(ASSET)] || assetLabel(ASSET);
    $("#modal-title").textContent = singular + " Detail";
    renderList($("#search").value);
    renderDetailCard();
    renderDetailTabs();
    renderDetailBody();
    $("#modal-overlay").classList.remove("hidden");
    setStatus("");
    loadFloods();
  } catch (err) {
    setStatus("Error: " + err.message, true);
  }
}

function closeModal() { $("#modal-overlay").classList.add("hidden"); }

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

// ---- asset switching -------------------------------------------------------

async function selectAsset(key) {
  ASSET = key;
  CURRENT_ID = null;
  closeModal();
  renderAssetTabs();
  const label = assetLabel(key);
  $("#sidebar-title").textContent = label;
  $("#content-title").textContent = label + " Portfolio";
  $("#search").value = "";
  setStatus("Loading " + label + "…");
  try {
    const [schemaRes, itemsRes] = await Promise.all([
      fetch(`/api/${key}/schema`),
      fetch(`/api/${key}/items`),
    ]);
    SCHEMA = await schemaRes.json();
    ITEMS = await itemsRes.json();
    renderList();
    renderSummary();
    setStatus("");
  } catch (err) {
    setStatus("Failed to load " + label + ": " + err.message, true);
  }
}

// ---- boot ------------------------------------------------------------------

async function boot() {
  setStatus("Loading…");
  try {
    ASSETS = await (await fetch("/api/assets")).json();
    $("#search").addEventListener("input", (e) => renderList(e.target.value));
    $("#modal-close").addEventListener("click", closeModal);
    $("#modal-expand").addEventListener("click", toggleExpand);
    $("#modal-overlay").addEventListener("click", (e) => {
      if (e.target.id === "modal-overlay") closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });
    // Default to Properties if present, else the first asset.
    const def = ASSETS.find((a) => a.key === "property") || ASSETS[0];
    if (def) await selectAsset(def.key);
  } catch (err) {
    setStatus("Failed to load: " + err.message, true);
  }
}

boot();
