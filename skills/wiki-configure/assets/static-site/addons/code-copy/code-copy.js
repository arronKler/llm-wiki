(() => {
  "use strict";

  const allOptions = window.LLM_WIKI_ADDON_OPTIONS || {};
  const options = allOptions["code-copy"] || {};
  const successDuration = Number.isInteger(options.success_duration_ms)
    ? Math.min(5000, Math.max(500, options.success_duration_ms))
    : 1600;

  const fallbackCopy = (text) => {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.className = "code-copy-fallback";
    document.body.append(textarea);
    textarea.select();
    let copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (_error) {
      copied = false;
    }
    textarea.remove();
    return copied;
  };

  const copyText = async (text) => {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (_error) {
        return fallbackCopy(text);
      }
    }
    return fallbackCopy(text);
  };

  document.querySelectorAll(".markdown-body pre > code").forEach((code, index) => {
    const block = code.parentElement;
    if (!block || block.querySelector(".code-copy-button")) return;
    block.classList.add("code-copy-block");

    const button = document.createElement("button");
    button.type = "button";
    button.className = "code-copy-button";
    button.textContent = "Copy";
    button.setAttribute("aria-label", `Copy code block ${index + 1}`);
    button.setAttribute("aria-live", "polite");

    let resetTimer;
    button.addEventListener("click", async () => {
      window.clearTimeout(resetTimer);
      const copied = await copyText(code.textContent || "");
      button.dataset.state = copied ? "success" : "error";
      button.textContent = copied ? "Copied" : "Copy failed";
      resetTimer = window.setTimeout(() => {
        button.removeAttribute("data-state");
        button.textContent = "Copy";
      }, successDuration);
    });
    block.append(button);
  });
})();
