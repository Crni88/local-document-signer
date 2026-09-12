"use strict";

const element = (id) => document.getElementById(id);
const state = {
  file: null, originalName: "", pages: [], page: 0, signature: null,
  style: "handwritten", color: "black", width: .28, zoom: 1,
  placements: [], selected: null, history: [], placing: false,
  uploading: false, downloading: false, loadingPage: false, dirty: false,
  pageImages: new Map(), pageRequest: 0, signatureRequest: 0,
};
let signatureTimer;
let resizing = false;

function showError(message) {
  element("error-message").textContent = message;
  element("error").hidden = false;
}

function clearError() { element("error").hidden = true; }
function setStatus(message) { element("status").textContent = message; }
function selectedPlacement() { return state.placements.find((placement) => placement.id === state.selected); }
function settings() { return { name: element("signer-name").value.trim(), style: state.style, color: state.color }; }

async function api(path, body, json = false) {
  const headers = { "X-Requested-With": "LocalSigner" };
  if (json) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { method: "POST", headers, body: json ? JSON.stringify(body) : body });
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    throw new Error(result.error || "The document could not be processed.");
  }
  return response;
}

function documentForm() {
  const form = new FormData();
  form.append("document", state.file);
  return form;
}

function updateControls() {
  const busy = state.uploading || state.downloading;
  const ready = Boolean(state.file) && !busy;
  element("open-file").disabled = busy;
  element("open-initial").disabled = busy;
  element("page-number").disabled = !ready;
  element("page-number").value = state.page + 1;
  element("page-number").max = state.pages.length || 1;
  element("page-total").textContent = state.pages.length;
  element("previous-page").disabled = !ready || state.page === 0;
  element("next-page").disabled = !ready || state.page >= state.pages.length - 1;
  element("place-signature").disabled = !ready || !state.signature || state.loadingPage;
  element("place-signature").setAttribute("aria-pressed", String(state.placing));
  element("undo").disabled = !ready || !state.history.length;
  element("delete-signature").disabled = !ready || !selectedPlacement();
  element("download").disabled = !ready || !state.signature || !state.placements.length;
  element("download-label").textContent = state.downloading ? "Preparing PDF..." : "Download signed PDF";
  element("signature-count").textContent = state.placements.length;
  element("zoom-in").disabled = !ready || state.zoom >= 2.5;
  element("zoom-out").disabled = !ready || state.zoom <= .5;
  element("fit-page").disabled = !ready;
  element("zoom-value").textContent = `${Math.round(state.zoom * 100)}%`;
  element("page-sheet").classList.toggle("placing", state.placing && Boolean(state.signature));
}

function checkpoint() {
  state.history.push(state.placements.map((placement) => ({ ...placement })));
  if (state.history.length > 40) state.history.shift();
  state.dirty = true;
}

function clampPlacement(placement) {
  const page = state.pages[placement.page];
  const ratio = state.signature.height / state.signature.width;
  const maximumWidth = Math.min(.95, .95 * page.height / (page.width * ratio));
  placement.width = Math.max(.01, Math.min(maximumWidth, placement.width));
  const height = placement.width * page.width * ratio / page.height;
  placement.x = Math.max(.001, Math.min(1 - placement.width - .001, placement.x));
  placement.y = Math.max(.001, Math.min(1 - height - .001, placement.y));
}

function positionElement(button, placement) {
  const page = state.pages[placement.page];
  button.style.left = `${placement.x * 100}%`;
  button.style.top = `${placement.y * 100}%`;
  button.style.width = `${placement.width * 100}%`;
  button.style.height = `${placement.width * page.width * state.signature.height / state.signature.width / page.height * 100}%`;
  button.classList.toggle("selected", placement.id === state.selected);
}

function selectPlacement(placement) {
  state.selected = placement.id;
  state.width = placement.width;
  element("signature-width").value = Math.round(state.width * 100);
  element("width-value").textContent = `${Math.round(state.width * 100)}%`;
  for (const button of element("placements").children) button.classList.toggle("selected", button.dataset.id === placement.id);
  updateControls();
}

function startDrag(event, placement, button) {
  if (event.button !== 0) return;
  event.preventDefault();
  event.stopPropagation();
  selectPlacement(placement);
  state.placing = false;
  updateControls();
  button.focus({ preventScroll: true });
  button.setPointerCapture(event.pointerId);
  button.classList.add("dragging");
  const bounds = element("page-sheet").getBoundingClientRect();
  const start = { pointerX: event.clientX, pointerY: event.clientY, left: placement.x, top: placement.y };
  let moved = false;
  button.onpointermove = (move) => {
    if (!moved && Math.abs(move.clientX - start.pointerX) + Math.abs(move.clientY - start.pointerY) < 3) return;
    if (!moved) checkpoint();
    moved = true;
    placement.x = start.left + (move.clientX - start.pointerX) / bounds.width;
    placement.y = start.top + (move.clientY - start.pointerY) / bounds.height;
    clampPlacement(placement);
    positionElement(button, placement);
  };
  button.onpointerup = button.onpointercancel = () => {
    button.classList.remove("dragging");
    button.onpointermove = null;
    button.onpointerup = null;
    button.onpointercancel = null;
    updateControls();
  };
}

function renderPlacements() {
  const container = element("placements");
  container.replaceChildren();
  if (!state.signature) return;
  for (const placement of state.placements.filter((item) => item.page === state.page)) {
    const button = document.createElement("button");
    button.className = "placed-signature";
    button.dataset.id = placement.id;
    button.setAttribute("aria-label", `Signature: ${settings().name}`);
    button.title = "Move signature";
    const image = document.createElement("img");
    image.src = `data:image/png;base64,${state.signature.image}`;
    image.alt = "";
    image.draggable = false;
    button.append(image);
    positionElement(button, placement);
    button.onpointerdown = (event) => startDrag(event, placement, button);
    button.onclick = (event) => { event.stopPropagation(); selectPlacement(placement); };
    button.onkeydown = (event) => {
      const directions = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
      if (!directions[event.key]) return;
      event.preventDefault();
      checkpoint();
      const step = event.shiftKey ? .02 : .002;
      const [horizontal, vertical] = directions[event.key];
      placement.x += horizontal * step;
      placement.y += vertical * step;
      clampPlacement(placement);
      selectPlacement(placement);
      positionElement(button, placement);
    };
    container.append(button);
  }
}

function fitPage() {
  const baseWidth = Math.max(160, Math.min(900, element("document-viewport").clientWidth - 48));
  element("page-sheet").style.width = `${baseWidth * state.zoom}px`;
}

async function showPage(pageNumber) {
  if (!state.file || pageNumber < 0 || pageNumber >= state.pages.length) return;
  const requestId = ++state.pageRequest;
  const file = state.file;
  state.page = pageNumber;
  state.selected = null;
  state.loadingPage = true;
  element("page-sheet").setAttribute("aria-busy", "true");
  setStatus(`Rendering page ${pageNumber + 1}...`);
  updateControls();
  try {
    let imageUrl = state.pageImages.get(pageNumber);
    if (!imageUrl) {
      const form = documentForm();
      form.append("page", pageNumber);
      const response = await api("/api/page", form);
      const image = await response.blob();
      if (file !== state.file) return;
      imageUrl = URL.createObjectURL(image);
      state.pageImages.set(pageNumber, imageUrl);
    }
    if (requestId !== state.pageRequest) return;
    const page = state.pages[pageNumber];
    element("page-sheet").style.aspectRatio = `${page.width} / ${page.height}`;
    element("page-image").src = imageUrl;
    element("page-image").alt = `Document page ${pageNumber + 1}`;
    element("page-sheet").setAttribute("aria-label", `Document page ${pageNumber + 1}`);
    element("empty-state").hidden = true;
    element("page-stage").hidden = false;
    fitPage();
    renderPlacements();
    element("document-viewport").scrollTop = 0;
    setStatus(`Page ${pageNumber + 1} of ${state.pages.length}`);
  } catch (error) {
    if (requestId === state.pageRequest) showError(error.message);
  } finally {
    if (requestId === state.pageRequest) {
      state.loadingPage = false;
      element("page-sheet").setAttribute("aria-busy", "false");
      updateControls();
    }
  }
}

async function uploadFile(file) {
  if (!file || state.uploading || state.downloading) return;
  if (file.size > 25 * 1024 * 1024) return showError("Choose a document smaller than 25 MB.");
  if (state.dirty && !confirm("Replace this document and discard its signature placements?")) return;
  clearError();
  state.uploading = true;
  updateControls();
  setStatus("Opening document...");
  try {
    const form = new FormData();
    form.append("document", file);
    const result = await (await api("/api/document", form)).json();
    if (result.digitallySigned && !confirm("This PDF already has a digital signature. Adding a visible signature can invalidate it. Continue?")) return;
    for (const url of state.pageImages.values()) URL.revokeObjectURL(url);
    state.pageImages.clear();
    state.file = result.pdf
      ? new File([Uint8Array.from(atob(result.pdf), (character) => character.charCodeAt(0))], result.filename, { type: "application/pdf" })
      : file;
    state.originalName = file.name;
    state.pages = result.pages;
    state.placements = [];
    state.history = [];
    state.selected = null;
    state.dirty = false;
    state.zoom = 1;
    state.placing = Boolean(state.signature);
    element("document-name").textContent = file.name;
    element("document-size").textContent = file.size >= 1024 * 1024 ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(file.size / 1024))} KB`;
    await showPage(0);
  } catch (error) {
    showError(error.message);
    setStatus(state.file ? `Page ${state.page + 1} of ${state.pages.length}` : "No document");
  } finally {
    state.uploading = false;
    updateControls();
  }
}

function scheduleSignature() {
  clearTimeout(signatureTimer);
  const requestId = ++state.signatureRequest;
  state.signature = null;
  if (state.placements.length) state.dirty = true;
  element("signature-preview").hidden = true;
  element("signature-placeholder").hidden = false;
  renderPlacements();
  updateControls();
  const name = settings().name;
  element("signature-display");
  document.querySelector(".signature-display").setAttribute("aria-busy", String(Boolean(name)));
  if (!name) return;
  signatureTimer = setTimeout(async () => {
    try {
      const signature = await (await api("/api/signature", settings(), true)).json();
      if (requestId !== state.signatureRequest) return;
      state.signature = signature;
      element("signature-preview").src = `data:image/png;base64,${signature.image}`;
      element("signature-preview").hidden = false;
      element("signature-placeholder").hidden = true;
      for (const placement of state.placements) clampPlacement(placement);
      if (!state.placements.length) state.placing = true;
      renderPlacements();
    } catch (error) {
      if (requestId === state.signatureRequest) showError(error.message);
    } finally {
      if (requestId === state.signatureRequest) {
        document.querySelector(".signature-display").setAttribute("aria-busy", "false");
        updateControls();
      }
    }
  }, 250);
}

function placeSignature(event) {
  if (!state.file || !state.signature || !state.placing || state.loadingPage || state.uploading || state.downloading) return;
  if (state.placements.length >= 50) return showError("This document already has 50 signatures.");
  checkpoint();
  const bounds = element("page-sheet").getBoundingClientRect();
  const page = state.pages[state.page];
  const height = state.width * page.width * state.signature.height / state.signature.width / page.height;
  const placement = {
    id: crypto.randomUUID(), page: state.page, width: state.width,
    x: (event.clientX - bounds.left) / bounds.width - state.width / 2,
    y: (event.clientY - bounds.top) / bounds.height - height / 2,
  };
  clampPlacement(placement);
  state.placements.push(placement);
  state.placing = false;
  selectPlacement(placement);
  renderPlacements();
  setStatus(`Signature placed on page ${state.page + 1}`);
  updateControls();
}

function deleteSelected() {
  if (!selectedPlacement()) return;
  checkpoint();
  state.placements = state.placements.filter((placement) => placement.id !== state.selected);
  state.selected = null;
  renderPlacements();
  updateControls();
}

async function downloadDocument() {
  if (!state.file || !state.signature || !state.placements.length || state.downloading) return;
  clearError();
  state.downloading = true;
  updateControls();
  try {
    const form = documentForm();
    for (const [key, value] of Object.entries(settings())) form.append(key, value);
    form.append("placements", JSON.stringify(state.placements));
    const response = await api("/api/sign", form);
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${state.originalName.replace(/\.[^.]+$/, "")}_signed.pdf`;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    state.dirty = false;
    setStatus("Signed PDF downloaded");
  } catch (error) { showError(error.message); }
  finally { state.downloading = false; updateControls(); }
}

for (const id of ["open-file", "open-initial"]) element(id).onclick = () => element("file-input").click();
element("file-input").onchange = (event) => { uploadFile(event.target.files[0]); event.target.value = ""; };
element("dismiss-error").onclick = clearError;
element("signer-name").oninput = scheduleSignature;
for (const button of document.querySelectorAll("[data-style], [data-color]")) {
  button.onclick = () => {
    const category = button.dataset.style ? "style" : "color";
    state[category] = button.dataset[category];
    for (const option of document.querySelectorAll(`[data-${category}]`)) option.setAttribute("aria-pressed", String(option === button));
    scheduleSignature();
  };
}
element("signature-width").oninput = (event) => {
  state.width = Number(event.target.value) / 100;
  element("width-value").textContent = `${event.target.value}%`;
  const placement = selectedPlacement();
  if (placement && state.signature) {
    if (!resizing) checkpoint();
    resizing = true;
    placement.width = state.width;
    clampPlacement(placement);
    renderPlacements();
    updateControls();
  }
};
element("signature-width").onchange = () => { resizing = false; };
element("previous-page").onclick = () => showPage(state.page - 1);
element("next-page").onclick = () => showPage(state.page + 1);
element("page-number").onchange = (event) => {
  const pageNumber = Number(event.target.value) - 1;
  if (Number.isInteger(pageNumber) && pageNumber >= 0 && pageNumber < state.pages.length) showPage(pageNumber);
  else updateControls();
};
element("place-signature").onclick = () => { state.placing = !state.placing; state.selected = null; renderPlacements(); updateControls(); };
element("page-sheet").onclick = placeSignature;
element("page-sheet").onkeydown = (event) => {
  if (event.target !== element("page-sheet") || !["Enter", " "].includes(event.key)) return;
  event.preventDefault();
  const bounds = element("page-sheet").getBoundingClientRect();
  placeSignature({ clientX: bounds.left + bounds.width / 2, clientY: bounds.top + bounds.height / 2 });
};
element("delete-signature").onclick = deleteSelected;
element("undo").onclick = () => {
  if (!state.history.length) return;
  state.placements = state.history.pop();
  if (state.signature) for (const placement of state.placements) clampPlacement(placement);
  state.selected = null;
  state.dirty = true;
  renderPlacements();
  updateControls();
};
element("download").onclick = downloadDocument;
for (const [id, change] of [["zoom-in", .25], ["zoom-out", -.25], ["fit-page", 0]]) {
  element(id).onclick = () => { state.zoom = change ? Math.max(.5, Math.min(2.5, state.zoom + change)) : 1; fitPage(); updateControls(); };
}
document.addEventListener("keydown", (event) => {
  if (!event.target.closest("input, textarea") && event.key === "Delete") deleteSelected();
});
document.addEventListener("dragover", (event) => { event.preventDefault(); document.body.classList.add("drag-over"); });
document.addEventListener("dragleave", (event) => { if (!event.relatedTarget) document.body.classList.remove("drag-over"); });
document.addEventListener("drop", (event) => {
  event.preventDefault();
  document.body.classList.remove("drag-over");
  const files = event.dataTransfer.files;
  if (files.length > 1) showError("Choose one document at a time.");
  else uploadFile(files[0]);
});
window.addEventListener("beforeunload", (event) => { if (state.dirty) { event.preventDefault(); event.returnValue = ""; } });
new ResizeObserver(fitPage).observe(element("document-viewport"));

const systemTheme = matchMedia("(prefers-color-scheme: dark)");
let theme = "system";
try { theme = localStorage.getItem("sign-theme") || "system"; } catch {}
function applyTheme() {
  document.documentElement.dataset.theme = theme === "system" ? (systemTheme.matches ? "dark" : "light") : theme;
  element("theme").setAttribute("aria-label", `Theme: ${theme}`);
  element("theme").title = `Theme: ${theme}`;
  element("theme").firstElementChild.textContent = { system: "desktop_windows", light: "light_mode", dark: "dark_mode" }[theme] || "desktop_windows";
}
element("theme").onclick = () => {
  theme = { system: "light", light: "dark", dark: "system" }[theme] || "system";
  try { localStorage.setItem("sign-theme", theme); } catch {}
  applyTheme();
};
systemTheme.addEventListener("change", applyTheme);
applyTheme();
updateControls();