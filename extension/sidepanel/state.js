// sidepanel/state.js

export class AppState {
  constructor() {
    this.status = "idle"; // idle | extracting | indexing | ready | answering | error | page_changed
    this.tabId = null;
    this.pageUrl = "";
    this.pageTitle = "";
    this.pageId = "";
    this.chunkCount = 0;
    this.truncated = false;
    this.extractedText = "";
    this.messages = []; // [{ id, role: "user"|"assistant", text, sources, error, stopped }]
    this.error = null;
    this.settings = null;
    this.abortController = null;

    // Per-tab session map
    this.tabSessions = new Map();
  }

  saveCurrentTabSession() {
    if (!this.tabId) return;
    this.tabSessions.set(this.tabId, {
      pageUrl: this.pageUrl,
      pageTitle: this.pageTitle,
      pageId: this.pageId,
      chunkCount: this.chunkCount,
      truncated: this.truncated,
      extractedText: this.extractedText,
      messages: [...this.messages],
      status: this.status === "answering" ? "ready" : this.status,
    });
  }

  restoreTabSession(tabId, currentUrl) {
    this.tabId = tabId;
    const session = this.tabSessions.get(tabId);
    const cleanUrl = currentUrl ? currentUrl.split("#")[0] : "";

    if (session && session.pageUrl === cleanUrl) {
      this.pageUrl = session.pageUrl;
      this.pageTitle = session.pageTitle;
      this.pageId = session.pageId;
      this.chunkCount = session.chunkCount;
      this.truncated = session.truncated;
      this.extractedText = session.extractedText;
      this.messages = session.messages;
      this.status = session.status || "ready";
      this.error = null;
    } else if (session && session.pageUrl !== cleanUrl) {
      // User navigated within this tab
      this.pageUrl = cleanUrl;
      this.pageTitle = "";
      this.pageId = session.pageId;
      this.chunkCount = session.chunkCount;
      this.truncated = session.truncated;
      this.extractedText = session.extractedText;
      this.messages = session.messages;
      this.status = "page_changed";
      this.error = null;
    } else {
      // Fresh tab with no session
      this.reset(tabId, cleanUrl);
    }
  }

  reset(tabId = null, pageUrl = "") {
    this.status = "idle";
    this.tabId = tabId;
    this.pageUrl = pageUrl ? pageUrl.split("#")[0] : "";
    this.pageTitle = "";
    this.pageId = "";
    this.chunkCount = 0;
    this.truncated = false;
    this.extractedText = "";
    this.messages = [];
    this.error = null;
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}
