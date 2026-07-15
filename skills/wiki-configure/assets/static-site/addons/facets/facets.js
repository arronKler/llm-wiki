(() => {
  "use strict";

  const grid = document.querySelector(".card-grid");
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll(".knowledge-card"));
  if (!cards.length) return;

  const searchIndex = Array.isArray(window.LLM_WIKI_SEARCH_INDEX)
    ? window.LLM_WIKI_SEARCH_INDEX
    : [];
  const allOptions = window.LLM_WIKI_ADDON_OPTIONS || {};
  const options = allOptions.facets || {};
  const allowedFields = new Set(["type", "status", "domains"]);
  const requestedFields = Array.isArray(options.fields)
    ? options.fields.filter((field) => allowedFields.has(field))
    : ["type", "status", "domains"];
  const fields = Array.from(new Set(requestedFields));
  const showCounts = options.show_counts !== false;

  const normalizeHref = (value) => {
    const text = String(value || "").replace(/^\.\//, "");
    return text.split("#", 1)[0].split("?", 1)[0];
  };
  const indexByHref = new Map(
    searchIndex.map((entry) => [normalizeHref(entry.href), entry]),
  );
  const valuesFor = (entry, card, field) => {
    const raw = entry?.[field] ?? card.dataset[field] ?? "";
    const rawValues = Array.isArray(raw) ? raw : String(raw).split(",");
    return rawValues.map((value) => String(value).trim()).filter(Boolean);
  };

  const records = cards.map((card) => {
    const link = card.querySelector("h2 a");
    const entry = indexByHref.get(normalizeHref(link?.getAttribute("href"))) || null;
    return {
      card,
      values: Object.fromEntries(fields.map((field) => [field, valuesFor(entry, card, field)])),
    };
  });

  const fieldValues = new Map();
  fields.forEach((field) => {
    const values = new Set(records.flatMap((record) => record.values[field]));
    if (values.size) {
      fieldValues.set(field, Array.from(values).sort((left, right) => left.localeCompare(right)));
    }
  });
  if (!fieldValues.size) return;

  let host = document.querySelector("[data-addon-facets]");
  if (!host) {
    host = document.createElement("form");
    host.dataset.addonFacets = "";
    grid.before(host);
  }
  host.classList.add("addon-facets");
  host.setAttribute("aria-label", "Filter knowledge pages");
  host.addEventListener("submit", (event) => event.preventDefault());
  host.replaceChildren();

  const labels = { type: "Type", status: "Status", domains: "Domain" };
  const selections = new Map();
  fieldValues.forEach((values, field) => {
    const label = document.createElement("label");
    label.className = "facet-field";
    const labelText = document.createElement("span");
    labelText.textContent = labels[field];
    const select = document.createElement("select");
    select.dataset.facet = field;
    const all = document.createElement("option");
    all.value = "";
    all.textContent = `All ${labels[field].toLocaleLowerCase()}s`;
    select.append(all);
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      const count = records.filter((record) => record.values[field].includes(value)).length;
      option.textContent = showCounts ? `${value} (${count})` : value;
      select.append(option);
    });
    selections.set(field, select);
    label.append(labelText, select);
    host.append(label);
  });

  const reset = document.createElement("button");
  reset.type = "button";
  reset.className = "facet-reset";
  reset.textContent = "Reset";
  const count = document.createElement("p");
  count.className = "facet-count";
  count.setAttribute("aria-live", "polite");
  host.append(reset, count);

  const apply = () => {
    let visible = 0;
    records.forEach((record) => {
      const matches = Array.from(selections).every(
        ([field, select]) => !select.value || record.values[field].includes(select.value),
      );
      record.card.hidden = !matches;
      if (matches) visible += 1;
    });
    count.textContent = `${visible} of ${records.length} pages shown`;
  };

  selections.forEach((select) => select.addEventListener("change", apply));
  reset.addEventListener("click", () => {
    selections.forEach((select) => {
      select.value = "";
    });
    apply();
    const first = selections.values().next().value;
    if (first) first.focus();
  });
  apply();
})();
