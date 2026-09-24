// sidepanel/settings.js

const DEFAULT_SETTINGS = {
  backendUrl: "http://localhost:8000",
  answerStyle: "simple", // simple | detailed
  uiLanguage: "bn"       // bn | en
};

export async function loadSettings() {
  return new Promise((resolve) => {
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(DEFAULT_SETTINGS, (stored) => {
        resolve({ ...DEFAULT_SETTINGS, ...stored });
      });
    } else {
      resolve({ ...DEFAULT_SETTINGS });
    }
  });
}

export async function saveSettings(newSettings) {
  return new Promise((resolve) => {
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set(newSettings, () => {
        resolve(newSettings);
      });
    } else {
      resolve(newSettings);
    }
  });
}

export function normalizeBackendUrl(url) {
  if (!url) return DEFAULT_SETTINGS.backendUrl;
  let clean = url.trim();
  if (clean.endsWith("/")) {
    clean = clean.slice(0, -1);
  }
  return clean;
}

export async function testBackendHealth(backendUrl) {
  const base = normalizeBackendUrl(backendUrl);
  try {
    const res = await fetch(`${base}/health`, { method: "GET" });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: String(err) };
  }
}
