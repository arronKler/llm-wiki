(() => {
  "use strict";

  const graph = window.LLM_WIKI_GRAPH;
  if (!graph || !Array.isArray(graph.nodes) || !graph.nodes.length) return;

  const allOptions = window.LLM_WIKI_ADDON_OPTIONS || {};
  const options = allOptions.graph || {};
  const maxNodes = Number.isInteger(options.max_nodes)
    ? Math.min(1000, Math.max(1, options.max_nodes))
    : 250;
  const height = Number.isInteger(options.height)
    ? Math.min(720, Math.max(280, options.height))
    : 440;
  const showLabels = options.show_labels !== false;
  const root = document.body.dataset.root || "";
  const svgNamespace = "http://www.w3.org/2000/svg";
  const compareText = (left, right) => (left < right ? -1 : left > right ? 1 : 0);

  const nodes = graph.nodes
    .map((node) => ({
      id: String(node.id || ""),
      title: String(node.title || node.id || "Untitled"),
      type: String(node.type || "knowledge"),
      href: typeof node.href === "string" ? node.href : "",
    }))
    .filter((node) => node.id)
    .sort((left, right) => compareText(left.title, right.title) || compareText(left.id, right.id))
    .slice(0, maxNodes);
  if (!nodes.length) return;

  const safeFallbackHref = (id) =>
    `${root}pages/${id.split("/").map((part) => encodeURIComponent(part)).join("/")}.html`;
  const nodeHref = (node) => {
    const candidate = node.href.trim();
    if (!candidate || candidate.startsWith("/") || candidate.includes(":") || candidate.includes("\\")) {
      return safeFallbackHref(node.id);
    }
    return `${root}${candidate}`;
  };

  const byId = new Map(nodes.map((node) => [node.id, node]));
  const edges = (Array.isArray(graph.edges) ? graph.edges : [])
    .map((edge) => ({ source: String(edge.source || ""), target: String(edge.target || "") }))
    .filter((edge) => byId.has(edge.source) && byId.has(edge.target) && edge.source !== edge.target)
    .sort((left, right) =>
      compareText(left.source, right.source) || compareText(left.target, right.target),
    );

  const neighbors = new Map(nodes.map((node) => [node.id, new Set()]));
  edges.forEach((edge) => {
    neighbors.get(edge.source).add(edge.target);
    neighbors.get(edge.target).add(edge.source);
  });

  let host = document.querySelector("[data-addon-graph]");
  if (!host) {
    const home = document.querySelector(".home-hero");
    if (!home) return;
    host = document.createElement("section");
    host.dataset.addonGraph = "";
    const cards = document.querySelector(".card-grid");
    (cards || home).after(host);
  }
  host.classList.add("addon-graph");
  host.replaceChildren();

  const title = document.createElement("h2");
  title.textContent = "Knowledge graph";
  const lede = document.createElement("p");
  lede.className = "graph-lede";
  lede.textContent = "Explore how exported pages refer to one another.";
  const layout = document.createElement("div");
  layout.className = "graph-layout";

  const width = 920;
  const svg = document.createElementNS(svgNamespace, "svg");
  svg.classList.add("graph-canvas");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `Knowledge graph with ${nodes.length} pages and ${edges.length} links`);

  const centerX = width / 2;
  const centerY = height / 2;
  const maxRadius = Math.max(70, Math.min(width, height) * 0.39);
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  const positions = new Map();
  nodes.forEach((node, index) => {
    const progress = nodes.length === 1 ? 0 : Math.sqrt((index + 0.5) / nodes.length);
    const radius = nodes.length === 1 ? 0 : 45 + (maxRadius - 45) * progress;
    const angle = -Math.PI / 2 + index * goldenAngle;
    positions.set(node.id, {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    });
  });

  const edgeLayer = document.createElementNS(svgNamespace, "g");
  edgeLayer.setAttribute("aria-hidden", "true");
  edges.forEach((edge) => {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    const line = document.createElementNS(svgNamespace, "line");
    line.classList.add("graph-edge");
    line.setAttribute("x1", String(source.x));
    line.setAttribute("y1", String(source.y));
    line.setAttribute("x2", String(target.x));
    line.setAttribute("y2", String(target.y));
    edgeLayer.append(line);
  });
  svg.append(edgeLayer);

  const details = document.createElement("aside");
  details.className = "graph-details";
  details.setAttribute("aria-live", "polite");
  const detailsTitle = document.createElement("h3");
  const detailsMeta = document.createElement("p");
  const detailsLinks = document.createElement("ul");
  details.append(detailsTitle, detailsMeta, detailsLinks);

  const showDetails = (node) => {
    const related = Array.from(neighbors.get(node.id) || [])
      .map((id) => byId.get(id))
      .filter(Boolean)
      .sort((left, right) => compareText(left.title, right.title) || compareText(left.id, right.id));
    detailsTitle.textContent = node.title;
    detailsMeta.textContent = `${node.type} · ${related.length} connection${related.length === 1 ? "" : "s"}`;
    detailsLinks.replaceChildren();
    if (!related.length) {
      const item = document.createElement("li");
      item.textContent = "No linked pages in this export.";
      detailsLinks.append(item);
      return;
    }
    related.forEach((relatedNode) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = nodeHref(relatedNode);
      link.textContent = relatedNode.title;
      item.append(link);
      detailsLinks.append(item);
    });
  };

  const nodeLayer = document.createElementNS(svgNamespace, "g");
  nodes.forEach((node) => {
    const position = positions.get(node.id);
    const link = document.createElementNS(svgNamespace, "a");
    link.classList.add("graph-node");
    link.setAttribute("href", nodeHref(node));
    link.setAttribute("aria-label", `${node.title}, ${neighbors.get(node.id).size} connections`);
    link.addEventListener("focus", () => showDetails(node));
    link.addEventListener("pointerenter", () => showDetails(node));

    const circle = document.createElementNS(svgNamespace, "circle");
    circle.setAttribute("cx", String(position.x));
    circle.setAttribute("cy", String(position.y));
    circle.setAttribute("r", String(Math.min(13, 7 + Math.sqrt(neighbors.get(node.id).size + 1))));
    const tooltip = document.createElementNS(svgNamespace, "title");
    tooltip.textContent = node.title;
    circle.append(tooltip);
    link.append(circle);

    if (showLabels && nodes.length <= 80) {
      const label = document.createElementNS(svgNamespace, "text");
      label.setAttribute("x", String(position.x + 12));
      label.setAttribute("y", String(position.y - 10));
      label.textContent = node.title.length > 26 ? `${node.title.slice(0, 25)}…` : node.title;
      link.append(label);
    }
    nodeLayer.append(link);
  });
  svg.append(nodeLayer);
  layout.append(svg, details);
  host.append(title, lede, layout);

  if (graph.nodes.length > nodes.length) {
    const note = document.createElement("p");
    note.className = "graph-limit-note";
    note.textContent = `Showing ${nodes.length} of ${graph.nodes.length} pages.`;
    host.append(note);
  }

  const accessible = document.createElement("details");
  accessible.className = "graph-accessible-list";
  const summary = document.createElement("summary");
  summary.textContent = "Browse graph as a page list";
  const list = document.createElement("ul");
  nodes.forEach((node) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = nodeHref(node);
    link.textContent = `${node.title} (${neighbors.get(node.id).size})`;
    item.append(link);
    list.append(item);
  });
  accessible.append(summary, list);
  host.append(accessible);
  showDetails(nodes[0]);
})();
