// background.js - Cross-browser service worker
const isSidePanelSupported =
  typeof chrome !== "undefined" &&
  chrome.sidePanel &&
  typeof chrome.sidePanel.setPanelBehavior === "function";

if (isSidePanelSupported) {
  // Chromium browsers: Open side panel automatically on action icon click
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});

  chrome.runtime.onInstalled.addListener(() => {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
  });
}

// Fallback for browsers that require explicit click handling (Firefox, older Chromium)
const actionApi =
  typeof chrome !== "undefined" && chrome.action
    ? chrome.action
    : typeof browser !== "undefined" && browser.action
    ? browser.action
    : null;

if (actionApi && actionApi.onClicked) {
  actionApi.onClicked.addListener(async (tab) => {
    if (typeof browser !== "undefined" && browser.sidebarAction && typeof browser.sidebarAction.toggle === "function") {
      browser.sidebarAction.toggle().catch(() => {});
    } else if (typeof chrome !== "undefined" && chrome.sidePanel && typeof chrome.sidePanel.open === "function" && tab?.windowId) {
      chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
    }
  });
}

