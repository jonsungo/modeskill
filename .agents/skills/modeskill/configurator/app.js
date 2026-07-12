const dimensions = ["typography", "color semantics", "spacing", "components", "forms", "modal behavior", "responsive behavior", "engineering conventions"];
const classifications = ["inherited", "adapted", "project-specific", "unresolved", "deprecated"];
const excludedDirectories = [".git", "node_modules", "vendor", "dist", "build", ".next", "coverage", "__pycache__", ".venv", "tmp", "temp", ".cache"];
const supportedLanguages = ["zh-CN", "en"];
let projects = [];
let modules = [];
let discoveredAt = "1970-01-01T00:00:00Z";
let localModulesPath = "";
let statusMessage = null;
let discoveryMessage = { key: "noDiscovery", parameters: {} };
let helpSequence = 0;

const byId = (id) => document.getElementById(id);
const values = (id) => byId(id).value.split(/[\n,]/).map((value) => value.trim()).filter(Boolean);

function normalizeLanguage(value) {
  return supportedLanguages.includes(value) ? value : "zh-CN";
}

const storedLanguage = localStorage.getItem("modeskill-language");
let language = normalizeLanguage(storedLanguage);
if (storedLanguage && storedLanguage !== language) localStorage.setItem("modeskill-language", language);

function t(key, parameters = {}) {
  const parts = key.split(".");
  let value = window.MODESKILL_I18N[language];
  for (const part of parts) value = value?.[part];
  if (typeof value !== "string") value = key;
  return value.replace(/\{(\w+)\}/g, (_, name) => String(parameters[name] ?? ""));
}

function applyLanguage(nextLanguage, persist = true) {
  language = normalizeLanguage(nextLanguage);
  document.documentElement.lang = language;
  byId("language").replaceChildren(...supportedLanguages.map((value) => new Option(window.MODESKILL_I18N[language].languageNames[value], value)));
  byId("language").value = language;
  if (persist) localStorage.setItem("modeskill-language", language);
  document.querySelectorAll("[data-i18n]").forEach((element) => { element.textContent = t(element.dataset.i18n); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => { element.placeholder = t(element.dataset.i18nPlaceholder); });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => { element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel)); });
  document.title = t("pageTitle");
  renderLanguageControl();
  renderDimensions();
  renderModules();
  renderStatus();
  renderDiscoveryStatus();
  updateHelpButtons();
}

function renderDimensions() {
  const selected = new Set([...byId("dimensions").querySelectorAll("input:checked")].map((input) => input.value));
  byId("dimensions").replaceChildren(...dimensions.map((dimension) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = dimension;
    input.checked = selected.size === 0 || selected.has(dimension);
    const text = document.createElement("span");
    text.textContent = t(`dimensions.${dimension}`);
    label.append(input, text);
    return label;
  }));
}

function renderLanguageControl() {
  byId("language-current").textContent = window.MODESKILL_I18N[language].languageNames[language];
  byId("language-trigger").setAttribute("aria-label", t("languageMenuLabel"));
  byId("language-menu").replaceChildren(...supportedLanguages.map((value) => {
    const button = document.createElement("button");
    button.type = "button";
    button.role = "menuitemradio";
    button.className = "language-option";
    button.dataset.language = value;
    button.setAttribute("aria-checked", String(value === language));
    button.textContent = window.MODESKILL_I18N[language].languageNames[value];
    button.addEventListener("click", () => {
      applyLanguage(value);
      closeLanguageMenu();
      byId("language-trigger").focus();
    });
    return button;
  }));
}

function setLanguageMenu(open) {
  byId("language-menu").hidden = !open;
  byId("language-trigger").setAttribute("aria-expanded", String(open));
}

function closeLanguageMenu() {
  setLanguageMenu(false);
}

function setStatus(key, parameters = {}) {
  statusMessage = { key, parameters };
  renderStatus();
}

function renderStatus() {
  const message = byId("message");
  message.textContent = statusMessage ? t(statusMessage.key, statusMessage.parameters) : "";
  message.dataset.state = statusMessage?.key.startsWith("errors.") ? "error" : statusMessage ? "success" : "idle";
}

function setDiscoveryStatus(key, parameters = {}) {
  discoveryMessage = { key, parameters };
  renderDiscoveryStatus();
}

function renderDiscoveryStatus() {
  const status = byId("discovery-status");
  status.textContent = t(discoveryMessage.key, discoveryMessage.parameters);
  status.dataset.state = discoveryMessage.key.startsWith("errors.") ? "error" : discoveryMessage.key === "discoveryResult" ? "success" : "neutral";
}

async function withBusyState(button, busyKey, operation) {
  const originalKey = button.dataset.i18n;
  const originalText = button.textContent;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.textContent = t(busyKey);
  try { return await operation(); }
  finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.textContent = originalKey ? t(originalKey) : originalText;
  }
}

function errorKey(error) {
  const key = `errors.${error?.code || "invalid_response"}`;
  return t(key) === key ? "errors.invalid_response" : key;
}

function manualProjects() {
  return values("manual-projects").map((path) => ({ name: path.split("/").filter(Boolean).at(-1) || t("workspaceFallbackName"), path }));
}

function selectedValues(select) {
  return [...select.selectedOptions].map((option) => option.value);
}

function configuration() {
  return {
    $schema: "../../shared/schemas/workspace.schema.json", schemaVersion: "0.1",
    workspace: { name: byId("workspace-name").value.trim(), root: byId("workspace-root").value.trim(), access_mode: "read-only" },
    discovery: {
      automatic: true, recursive: byId("recursive").checked, max_depth: Number(byId("max-depth").value),
      treat_workspace_root_as_project: byId("root-project").checked, continue_below_repository_root: byId("continue-below").checked,
      project_markers: values("markers"), include_patterns: values("includes"), exclude_patterns: values("excludes"), excluded_directories: excludedDirectories
    },
    manual_projects: manualProjects(), discovery_cache: { discovered_at: discoveredAt, discovered_projects: projects },
    roles: { primary_reference: byId("primary-reference").value, secondary_references: selectedValues(byId("secondary-references")), target_project: byId("target-project").value },
    analysis: { dimensions: [...byId("dimensions").querySelectorAll("input:checked")].map((input) => input.value), classifications, require_evidence: true },
    authorization: { workspace_access: "read-only", reference_access: "read-only", target_default_access: "read-only", target_write_policy: byId("allow-write-request").checked ? "explicit-per-task" : "disabled" },
    authority_mapping: [], allowed_variations: []
  };
}

function renderProjects() {
  byId("project-list").replaceChildren(...projects.map((project) => {
    const item = document.createElement("div");
    item.textContent = `${project.name}  ${project.path}  [${t(`projectSource.${project.source}`)}]`;
    return item;
  }));
  for (const id of ["primary-reference", "secondary-references", "target-project"]) {
    const select = byId(id);
    const previous = selectedValues(select);
    select.replaceChildren(...projects.map((project) => new Option(project.name, project.id, false, previous.includes(project.id))));
  }
  updateJson();
}

function localized(object) {
  return object?.[language] || object?.["zh-CN"] || object?.en || "";
}

function renderModules() {
  if (!byId("module-list")) return;
  byId("local-modules-path").textContent = localModulesPath;
  byId("module-list").replaceChildren(...modules.map((module) => {
    const card = document.createElement("article");
    card.className = "module-card";
    const heading = document.createElement("div");
    heading.className = "module-heading";
    const title = document.createElement("h3");
    title.textContent = localized(module.display_name) || module.id;
    const strategy = document.createElement("span");
    strategy.className = `strategy ${module.distribution === "git-synced" ? "synced" : "local"}`;
    const strategyKey = module.distribution === "git-synced" ? "gitSynced" : "localOnly";
    strategy.textContent = t(strategyKey);
    const strategyWrap = document.createElement("span");
    strategyWrap.className = "strategy-wrap";
    strategyWrap.append(strategy, createHelpControl(strategyKey));
    heading.append(title, strategyWrap);
    const description = document.createElement("p");
    description.textContent = localized(module.description);
    const facts = document.createElement("dl");
    const status = module.installed === false ? t("missing") : module.enabled ? t("enabled") : t("disabled");
    for (const [label, value] of [[t("moduleStatus"), status], [t("moduleDistribution"), strategy.textContent], [t("modulePath"), module.path], [t("moduleImplementation"), module.implemented === false ? t("notImplemented") : t("implemented")]]) {
      const term = document.createElement("dt"); term.textContent = label;
      const detail = document.createElement("dd"); detail.textContent = value;
      facts.append(term, detail);
    }
    card.append(heading, description, facts);
    if (module.distribution === "local-only" && module.installed !== false) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = module.enabled ? "danger-secondary" : "secondary";
      button.textContent = t(module.enabled ? "disableModule" : "enableModule");
      button.addEventListener("click", () => withBusyState(button, "processing", () => toggleModule(module.id, !module.enabled)));
      card.append(button);
    }
    return card;
  }));
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  let result;
  try { result = await response.json(); }
  catch (_) { const error = new Error("invalid_response"); error.code = "invalid_response"; throw error; }
  if (!response.ok) {
    const error = new Error(result?.error?.code || "invalid_response");
    error.code = result?.error?.code || "invalid_response";
    throw error;
  }
  return result;
}

async function loadModules() {
  try {
    const result = await request("/api/modules");
    modules = result.modules;
    localModulesPath = result.local_modules_path;
    renderModules();
  } catch (error) { setStatus(errorKey(error)); }
}

async function toggleModule(moduleId, enabled) {
  try {
    await request("/api/modules/toggle", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ module_id: moduleId, enabled }) });
    await loadModules();
    setStatus("moduleUpdated");
  } catch (error) { setStatus(errorKey(error)); }
}

byId("language").addEventListener("change", (event) => applyLanguage(event.target.value));
byId("language-trigger").addEventListener("click", () => setLanguageMenu(byId("language-menu").hidden));
document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest(".language")) closeLanguageMenu();
});
byId("discover").addEventListener("click", () => withBusyState(byId("discover"), "discovering", async () => {
  try {
    const result = await request("/api/discover", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(configuration()) });
    projects = result.projects; discoveredAt = result.discovered_at; renderProjects();
    setDiscoveryStatus("discoveryResult", { count: projects.length, rejected: result.rejected_paths.length });
  } catch (error) { setDiscoveryStatus(errorKey(error)); }
}));
byId("validate").addEventListener("click", () => withBusyState(byId("validate"), "validating", async () => {
  try { await request("/api/validate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(configuration()) }); setStatus("configValid"); }
  catch (error) { setStatus(errorKey(error)); }
}));
byId("save").addEventListener("click", () => withBusyState(byId("save"), "saving", async () => {
  try { const result = await request("/api/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(configuration()) }); setStatus("configSaved", { path: result.saved }); }
  catch (error) { setStatus(errorKey(error)); }
}));
byId("copy-modules-path").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(localModulesPath); setStatus("pathCopied"); }
  catch (error) { setStatus(errorKey(error)); }
});

function createHelpControl(helpKey) {
  const container = document.createElement("span");
  container.className = "help-control";
  const button = document.createElement("button");
  button.type = "button";
  button.className = "help-button";
  button.dataset.helpKey = helpKey;
  button.setAttribute("aria-expanded", "false");
  button.textContent = "?";
  container.append(button);
  initializeHelpButton(button);
  return container;
}

function initializeHelpButton(button) {
  if (button.dataset.helpReady === "true") return;
  button.dataset.helpReady = "true";
  const tooltip = document.createElement("span");
  tooltip.className = "help-tooltip";
  tooltip.id = `help-tooltip-${helpSequence++}`;
  tooltip.role = "tooltip";
  tooltip.hidden = true;
  button.setAttribute("aria-controls", tooltip.id);
  button.after(tooltip);
  const toggle = () => {
    const willOpen = tooltip.hidden;
    closeHelpTooltips(button);
    tooltip.hidden = !willOpen;
    button.setAttribute("aria-expanded", String(willOpen));
  };
  button.addEventListener("click", (event) => { event.preventDefault(); event.stopPropagation(); toggle(); });
  button.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); event.stopPropagation(); toggle(); }
    if (event.key === "Escape") { event.preventDefault(); tooltip.hidden = true; button.setAttribute("aria-expanded", "false"); }
  });
  updateHelpButton(button);
}

function closeHelpTooltips(exceptButton = null) {
  document.querySelectorAll(".help-button").forEach((button) => {
    if (button === exceptButton) return;
    const tooltip = document.getElementById(button.getAttribute("aria-controls"));
    if (tooltip) tooltip.hidden = true;
    button.setAttribute("aria-expanded", "false");
  });
}

function updateHelpButton(button) {
  const helpKey = button.dataset.helpKey;
  const term = t(`helpTerms.${helpKey}`);
  button.setAttribute("aria-label", t("helpLabel", { term }));
  const tooltip = document.getElementById(button.getAttribute("aria-controls"));
  if (tooltip) tooltip.textContent = t(`help.${helpKey}`);
}

function updateHelpButtons() {
  document.querySelectorAll(".help-button").forEach(updateHelpButton);
}

document.querySelectorAll(".help-button").forEach(initializeHelpButton);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeHelpTooltips();
    closeLanguageMenu();
  }
});
document.addEventListener("input", updateJson);
function updateJson() { byId("json-output").textContent = JSON.stringify(configuration(), null, 2); }

window.ModeskillLanguage = { normalizeLanguage, applyLanguage };
applyLanguage(language, false);
updateJson();
loadModules();
