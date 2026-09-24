// sidepanel/page.js

export async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab || null;
}

export function isRestrictedUrl(url) {
  if (!url) return true;
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return true;
    }
    const host = parsed.hostname.toLowerCase();
    if (
      host === "chrome.google.com" ||
      host === "chromewebstore.google.com"
    ) {
      return true;
    }
    // PDF detection
    if (parsed.pathname.toLowerCase().endsWith(".pdf")) {
      return true;
    }
    return false;
  } catch (e) {
    return true;
  }
}

export async function extractActivePage(tabId, tabUrl) {
  if (isRestrictedUrl(tabUrl)) {
    return { ok: false, reason: "restricted" };
  }

  try {
    // 1. Inject Readability and extractor script
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["lib/Readability.js", "content/extract.js"],
    });

    // 2. Call extraction function
    const [response] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => (window.__bpeExtractPage ? window.__bpeExtractPage() : null),
    });

    if (!response || !response.result) {
      return { ok: false, reason: "generic" };
    }

    return response.result;
  } catch (err) {
    console.warn("[Bangla Page Explainer] executeScript failed:", err);
    return { ok: false, reason: "restricted", error: String(err) };
  }
}

export async function getSelectionFromPage(tabId) {
  try {
    const [response] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => (window.__bpeGetSelection ? window.__bpeGetSelection() : ""),
    });
    return response?.result || "";
  } catch (err) {
    console.warn("[Bangla Page Explainer] Failed to get selection:", err);
    return "";
  }
}

export async function highlightInPage(tabId, snippet) {
  try {
    const [response] = await chrome.scripting.executeScript({
      target: { tabId },
      func: (text) => (window.__bpeHighlight ? window.__bpeHighlight(text) : false),
      args: [snippet],
    });
    return Boolean(response?.result);
  } catch (err) {
    console.warn("[Bangla Page Explainer] Failed to highlight in page:", err);
    return false;
  }
}
