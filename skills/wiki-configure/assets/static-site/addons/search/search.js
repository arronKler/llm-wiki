(() => {
  "use strict";

  const index = Array.isArray(window.LLM_WIKI_SEARCH_INDEX)
    ? window.LLM_WIKI_SEARCH_INDEX
    : [];
  const input = document.querySelector("[data-search-input]");
  const results = document.querySelector("[data-search-results]");
  const root = document.body.dataset.root || "";
  const allOptions = window.LLM_WIKI_ADDON_OPTIONS || {};
  const options = allOptions.search || {};
  const maxResults = Number.isInteger(options.max_results)
    ? Math.min(50, Math.max(1, options.max_results))
    : 12;
  const shortcut = options.shortcut === "none" ? "none" : "/";

  if (!input || !results) return;

  const resultsId = results.id || "wiki-search-results";
  results.id = resultsId;
  results.setAttribute("role", "listbox");
  results.setAttribute("aria-label", "Search results");
  input.setAttribute("aria-controls", resultsId);
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");

  let activeIndex = -1;

  const localHref = (value) => {
    const candidate = String(value || "").trim();
    if (!candidate || candidate.startsWith("/") || candidate.includes(":") || candidate.includes("\\")) {
      return `${root}index.html`;
    }
    return `${root}${candidate}`;
  };

  const resultLinks = () => Array.from(results.querySelectorAll("a.search-result"));

  const setActive = (nextIndex) => {
    const links = resultLinks();
    if (!links.length) {
      activeIndex = -1;
      input.removeAttribute("aria-activedescendant");
      return;
    }
    activeIndex = Math.max(0, Math.min(nextIndex, links.length - 1));
    links.forEach((link, indexValue) => {
      link.setAttribute("aria-selected", indexValue === activeIndex ? "true" : "false");
    });
    input.setAttribute("aria-activedescendant", links[activeIndex].id);
    links[activeIndex].scrollIntoView({ block: "nearest" });
  };

  const close = () => {
    activeIndex = -1;
    results.hidden = true;
    results.replaceChildren();
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };

  const render = (query) => {
    const terms = query
      .normalize("NFKC")
      .toLocaleLowerCase()
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    if (!terms.length) {
      close();
      return;
    }

    const matches = index
      .map((entry) => {
        const title = String(entry.title || "");
        const haystack = `${title} ${entry.type || ""} ${entry.summary || ""} ${entry.text || ""}`
          .normalize("NFKC")
          .toLocaleLowerCase();
        if (!terms.every((term) => haystack.includes(term))) return null;
        const titleLower = title.normalize("NFKC").toLocaleLowerCase();
        const score = terms.reduce(
          (total, term) => total + (titleLower.includes(term) ? 10 : 1),
          0,
        );
        return { entry, score };
      })
      .filter(Boolean)
      .sort(
        (left, right) =>
          right.score - left.score ||
          String(left.entry.title).localeCompare(String(right.entry.title)),
      )
      .slice(0, maxResults);

    activeIndex = -1;
    results.replaceChildren();
    if (!matches.length) {
      const empty = document.createElement("p");
      empty.className = "search-result search-empty";
      empty.textContent = "No matching pages";
      results.append(empty);
    } else {
      matches.forEach(({ entry }, resultIndex) => {
        const link = document.createElement("a");
        link.id = `wiki-search-result-${resultIndex}`;
        link.className = "search-result";
        link.href = localHref(entry.href);
        link.setAttribute("role", "option");
        link.setAttribute("aria-selected", "false");

        const title = document.createElement("strong");
        title.textContent = String(entry.title || entry.id || "Untitled");
        const summary = document.createElement("small");
        summary.textContent = String(entry.summary || entry.type || "Knowledge page");
        link.append(title, summary);
        results.append(link);
      });
    }
    results.hidden = false;
    input.setAttribute("aria-expanded", "true");
  };

  input.addEventListener("input", () => render(input.value));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      input.value = "";
      close();
      input.blur();
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (!resultLinks().length) return;
      event.preventDefault();
      const delta = event.key === "ArrowDown" ? 1 : -1;
      const start = activeIndex < 0 ? (delta > 0 ? 0 : resultLinks().length - 1) : activeIndex + delta;
      setActive(start);
      return;
    }
    if (event.key === "Enter" && activeIndex >= 0) {
      const active = resultLinks()[activeIndex];
      if (active) active.click();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (shortcut !== "/" || event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) return;
    const tag = document.activeElement?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    event.preventDefault();
    input.focus();
  });

  document.addEventListener("click", (event) => {
    if (!results.contains(event.target) && event.target !== input) close();
  });
})();
