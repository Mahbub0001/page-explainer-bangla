// content/extract.js
// Guard against duplicate injection
(function () {
  if (window.__bpeExtractorInjected) return;
  window.__bpeExtractorInjected = true;

  const BLOCK_TAGS = new Set([
    "P", "DIV", "SECTION", "ARTICLE", "LI",
    "H1", "H2", "H3", "H4", "H5", "H6",
    "PRE", "BLOCKQUOTE", "TR", "BR", "HEADER", "FOOTER", "MAIN"
  ]);

  const HEADING_TAGS = new Set(["H1", "H2", "H3", "H4", "H5", "H6"]);

  const IGNORE_TAGS = new Set([
    "SCRIPT", "STYLE", "NOSCRIPT", "NAV", "FOOTER",
    "HEADER", "ASIDE", "FORM", "IFRAME", "SVG",
    "BUTTON", "SELECT", "TEXTAREA"
  ]);

  function isVisible(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) return false;
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") {
      return false;
    }
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function htmlToText(rootNode) {
    const pieces = [];

    function walk(node) {
      if (!node) return;

      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.nodeValue;
        if (text) {
          // Replace tabs/multiple spaces with single space
          const clean = text.replace(/[\t\r\f ]+/g, " ");
          pieces.push(clean);
        }
        return;
      }

      if (node.nodeType === Node.ELEMENT_NODE) {
        const tagName = node.tagName.toUpperCase();

        if (IGNORE_TAGS.has(tagName)) return;
        if (node.getAttribute("aria-hidden") === "true" || node.hasAttribute("hidden")) return;

        const isHeading = HEADING_TAGS.has(tagName);
        const isLi = tagName === "LI";
        const isBlock = BLOCK_TAGS.has(tagName);

        if (isHeading) {
          pieces.push("\n# ");
        } else if (isLi) {
          pieces.push("\n- ");
        } else if (isBlock) {
          pieces.push("\n");
        }

        for (const child of node.childNodes) {
          walk(child);
        }

        if (isBlock) {
          pieces.push("\n");
        }
      }
    }

    walk(rootNode);

    // Post-process string
    let result = pieces.join("");
    // Collapse horizontal spaces
    result = result.replace(/[ \t]+/g, " ");
    // Collapse lines with only whitespace
    result = result.replace(/\n +/g, "\n").replace(/ +\n/g, "\n");
    // Collapse 3 or more newlines to 2
    result = result.replace(/\n{3,}/g, "\n\n");
    return result.trim();
  }

  function fallbackExtract() {
    const container =
      document.querySelector("article") ||
      document.querySelector("main") ||
      document.querySelector('[role="main"]') ||
      document.body;

    if (!container) return "";
    return htmlToText(container);
  }

  window.__bpeExtractPage = function () {
    try {
      const url = window.location.href.split("#")[0];
      const lang = document.documentElement.lang || "";

      // 1. Login-page guard: check for visible password input
      const passwordInputs = document.querySelectorAll('input[type="password"]');
      for (const input of passwordInputs) {
        if (isVisible(input)) {
          return { ok: false, reason: "login_page", url, title: document.title };
        }
      }

      let extractedTitle = document.title || "";
      let extractedText = "";

      // 2. Try Mozilla Readability if available
      if (typeof Readability === "function") {
        try {
          const documentClone = document.cloneNode(true);
          const reader = new Readability(documentClone);
          const article = reader.parse();

          if (article && article.content) {
            extractedTitle = article.title || document.title || "";
            const parser = new DOMParser();
            const doc = parser.parseFromString(article.content, "text/html");
            extractedText = htmlToText(doc.body);
          }
        } catch (e) {
          console.warn("[Bangla Page Explainer] Readability parsing failed, falling back:", e);
        }
      }

      // 3. Fallback if Readability returned empty or < 200 chars
      if (!extractedText || extractedText.length < 200) {
        const fallbackText = fallbackExtract();
        if (fallbackText.length > extractedText.length) {
          extractedText = fallbackText;
        }
      }

      // 4. Truncation to 120,000 characters
      const MAX_CHARS = 120000;
      let truncated = false;
      if (extractedText.length > MAX_CHARS) {
        extractedText = extractedText.slice(0, MAX_CHARS);
        truncated = true;
      }

      return {
        ok: true,
        url,
        title: extractedTitle,
        text: extractedText,
        lang,
        truncated,
      };
    } catch (err) {
      console.error("[Bangla Page Explainer] Page extraction error:", err);
      return { ok: false, reason: "generic", error: String(err) };
    }
  };

  window.__bpeGetSelection = function () {
    try {
      const sel = window.getSelection();
      if (!sel) return "";
      return sel.toString().trim().slice(0, 4000);
    } catch (e) {
      return "";
    }
  };

  window.__bpeHighlight = function (snippet) {
    try {
      if (!snippet || typeof window.find !== "function") return false;

      // Normalize whitespace
      const normalized = snippet.replace(/\s+/g, " ").trim();
      if (!normalized) return false;

      // Extract longest line or substring
      const lines = normalized.split(/[\n।.]/).map(l => l.trim()).filter(Boolean);
      const targetStr = lines.reduce((a, b) => (a.length >= b.length ? a : b), normalized);

      const lengths = [60, 40, 25];
      for (const len of lengths) {
        const sub = targetStr.slice(0, len).trim();
        if (sub.length < 10) continue;

        // Reset selection before searching
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges();

        // window.find(aString, aCaseSensitive, aBackwards, aWrapAround, aWholeWord, aSearchInFrames, aShowDialog)
        const found = window.find(sub, false, false, true, false, false, false);
        if (found) {
          const currentSel = window.getSelection();
          if (currentSel && currentSel.rangeCount > 0) {
            const range = currentSel.getRangeAt(0);
            const parent = range.commonAncestorContainer.nodeType === Node.ELEMENT_NODE
              ? range.commonAncestorContainer
              : range.commonAncestorContainer.parentElement;
            if (parent && typeof parent.scrollIntoView === "function") {
              parent.scrollIntoView({ behavior: "smooth", block: "center" });
            }
          }
          return true;
        }
      }
      return false;
    } catch (err) {
      console.warn("[Bangla Page Explainer] Highlight error (ignored):", err);
      return false;
    }
  };
})();
