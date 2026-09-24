// sidepanel/render.js
import { t } from "./i18n.js";

/**
 * Render text containing inline formatting: **bold** and [n] source chips.
 * Pure DOM construction without innerHTML for absolute XSS security.
 */
function renderInlineFormatting(text, container, sources, onSourceClick) {
  // Regex to match **bold** or [1..99]
  const pattern = /(\*\*[^*]+\*\*|\[\d{1,2}\])/g;
  let lastIndex = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    // Add text preceding the match
    if (match.index > lastIndex) {
      container.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
    }

    const token = match[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      const strong = document.createElement("strong");
      strong.textContent = token.slice(2, -2);
      container.appendChild(strong);
    } else if (token.startsWith("[") && token.endsWith("]")) {
      const srcId = parseInt(token.slice(1, -1), 10);
      const hasSource = sources && sources.some((s) => s.id === srcId);

      if (hasSource) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "src-chip";
        btn.textContent = token;
        btn.title = t("sources");
        btn.setAttribute("aria-label", `${t("sources")} ${srcId}`);
        btn.addEventListener("click", () => {
          if (onSourceClick) onSourceClick(srcId);
        });
        container.appendChild(btn);
      } else {
        container.appendChild(document.createTextNode(token));
      }
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    container.appendChild(document.createTextNode(text.slice(lastIndex)));
  }
}

/**
 * Render structured markdown subset (paragraphs, bullet lists, bold, source chips).
 */
export function renderMarkdownSubset(rawText, targetEl, sources = [], onSourceClick = null) {
  while (targetEl.firstChild) {
    targetEl.removeChild(targetEl.firstChild);
  }

  if (!rawText) return;

  const paragraphs = rawText.split(/\n\n+/);

  for (const para of paragraphs) {
    const lines = para.split("\n");
    let currentUl = null;

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        if (!currentUl) {
          currentUl = document.createElement("ul");
          currentUl.className = "msg-list";
          targetEl.appendChild(currentUl);
        }
        const li = document.createElement("li");
        renderInlineFormatting(trimmed.slice(2), li, sources, onSourceClick);
        currentUl.appendChild(li);
      } else {
        currentUl = null;
        if (trimmed) {
          const p = document.createElement("p");
          p.className = "msg-p";
          renderInlineFormatting(trimmed, p, sources, onSourceClick);
          targetEl.appendChild(p);
        }
      }
    }
  }
}

/**
 * Render a complete message bubble into the chat list.
 */
export function renderMessageElement(msg, onSourceClick, onViewInPage) {
  const wrapper = document.createElement("div");
  wrapper.className = `chat-bubble chat-${msg.role}`;
  wrapper.id = `msg-${msg.id}`;

  const bodyEl = document.createElement("div");
  bodyEl.className = "msg-content";
  wrapper.appendChild(bodyEl);

  renderMarkdownSubset(msg.text, bodyEl, msg.sources, onSourceClick);

  // If streaming and this is the active message, add streaming cursor
  if (msg.streaming) {
    const cursor = document.createElement("span");
    cursor.className = "streaming-cursor";
    cursor.textContent = "▍";
    bodyEl.appendChild(cursor);
  }

  // Stopped indicator
  if (msg.stopped) {
    const stoppedEl = document.createElement("div");
    stoppedEl.className = "msg-hint stopped-hint";
    stoppedEl.textContent = `[${t("stop")}]`;
    wrapper.appendChild(stoppedEl);
  }

  // Assistant footer: Copy button & Sources collapsible
  if (msg.role === "assistant") {
    const footer = document.createElement("div");
    footer.className = "msg-footer";

    // Copy button
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "btn-secondary btn-xs copy-btn";
    copyBtn.textContent = t("copy");
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(msg.text);
        copyBtn.textContent = t("copied");
        setTimeout(() => {
          copyBtn.textContent = t("copy");
        }, 2000);
      } catch (err) {
        console.warn("Copy failed:", err);
      }
    });
    footer.appendChild(copyBtn);

    // Collapsible sources
    if (msg.sources && msg.sources.length > 0) {
      const details = document.createElement("details");
      details.className = "sources-details";
      details.id = `sources-details-${msg.id}`;

      const summary = document.createElement("summary");
      summary.className = "sources-summary";
      summary.textContent = `${t("sources")} (${msg.sources.length})`;
      details.appendChild(summary);

      const list = document.createElement("div");
      list.className = "sources-list";

      msg.sources.forEach((source) => {
        const item = document.createElement("div");
        item.className = "source-item";
        item.id = `source-${msg.id}-${source.id}`;

        const header = document.createElement("div");
        header.className = "source-header";

        const badge = document.createElement("span");
        badge.className = "source-badge";
        badge.textContent = `[${source.id}]`;
        header.appendChild(badge);

        const viewBtn = document.createElement("button");
        viewBtn.type = "button";
        viewBtn.className = "btn-link btn-xs";
        viewBtn.textContent = t("view_in_page");
        viewBtn.addEventListener("click", () => {
          if (onViewInPage) onViewInPage(source.text);
        });
        header.appendChild(viewBtn);

        item.appendChild(header);

        const textDiv = document.createElement("div");
        textDiv.className = "source-text";
        textDiv.textContent = source.text;
        item.appendChild(textDiv);

        list.appendChild(item);
      });

      details.appendChild(list);
      footer.appendChild(details);
    }

    wrapper.appendChild(footer);
  }

  return wrapper;
}
