(() => {
  "use strict";

  const article = document.querySelector(".knowledge-page .markdown-body");
  if (!article) return;

  const allOptions = window.LLM_WIKI_ADDON_OPTIONS || {};
  const options = allOptions.toc || {};
  const requestedMin = Number.isInteger(options.min_level) ? options.min_level : 2;
  const requestedMax = Number.isInteger(options.max_level) ? options.max_level : 4;
  const minLevel = Math.min(6, Math.max(1, Math.min(requestedMin, requestedMax)));
  const maxLevel = Math.min(6, Math.max(minLevel, Math.max(requestedMin, requestedMax)));
  const selector = Array.from(
    { length: maxLevel - minLevel + 1 },
    (_, index) => `h${minLevel + index}`,
  ).join(",");
  const headings = Array.from(article.querySelectorAll(selector));
  if (!headings.length) return;

  const usedIds = new Set();
  headings.forEach((heading, index) => {
    let candidate = heading.id || `section-${index + 1}`;
    let unique = candidate;
    let suffix = 2;
    while (usedIds.has(unique)) {
      unique = `${candidate}-${suffix}`;
      suffix += 1;
    }
    heading.id = unique;
    usedIds.add(unique);
  });

  let host = document.querySelector("[data-addon-toc]");
  if (!host) {
    const sidebar = document.querySelector(".site-shell > aside");
    if (!sidebar) return;
    host = document.createElement("section");
    host.dataset.addonToc = "";
    sidebar.append(host);
  }
  host.classList.add("addon-toc");
  host.replaceChildren();

  const title = document.createElement("h2");
  title.textContent = "On this page";
  const nav = document.createElement("nav");
  nav.setAttribute("aria-label", "On this page");
  const list = document.createElement("ol");
  const links = [];

  headings.forEach((heading) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${encodeURIComponent(heading.id)}`;
    link.dataset.level = heading.tagName.slice(1);
    link.textContent = heading.textContent.trim() || "Untitled section";
    item.append(link);
    list.append(item);
    links.push(link);
  });
  nav.append(list);
  host.append(title, nav);

  let scheduled = false;
  const updateCurrent = () => {
    scheduled = false;
    let current = 0;
    headings.forEach((heading, index) => {
      if (heading.getBoundingClientRect().top <= 140) current = index;
    });
    links.forEach((link, index) => {
      if (index === current) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  };
  const scheduleUpdate = () => {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(updateCurrent);
  };

  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate, { passive: true });
  updateCurrent();
})();
