// sidepanel/sidepanel.js
import { AppState } from "./state.js";
import { t, setLanguage, getLanguage } from "./i18n.js";
import {
  loadSettings,
  saveSettings,
  testBackendHealth,
  normalizeBackendUrl
} from "./settings.js";
import {
  getActiveTab,
  extractActivePage,
  getSelectionFromPage,
  highlightInPage,
  isRestrictedUrl
} from "./page.js";
import { indexPage, streamPost, ApiError } from "./api.js";
import { renderMarkdownSubset, renderMessageElement } from "./render.js";

const state = new AppState();

// DOM Elements
const elAppTitle = document.getElementById("app-title");
const elPageTitle = document.getElementById("page-title");
const elBadgeChunks = document.getElementById("badge-chunks");
const elNoteTruncated = document.getElementById("note-truncated");
const elStatusText = document.getElementById("status-text");
const elBtnAnalyze = document.getElementById("btn-analyze");
const elBtnAnalyzeText = document.getElementById("btn-analyze-text");
const elBtnSummary = document.getElementById("btn-summary");
const elBtnExplainSelection = document.getElementById("btn-explain-selection");
const elAlertBox = document.getElementById("alert-box");
const elBanner = document.getElementById("page-changed-banner");
const elBannerText = document.getElementById("banner-text");
const elBtnBannerReanalyze = document.getElementById("btn-banner-reanalyze");
const elChatContainer = document.getElementById("chat-container");
const elEmptyState = document.getElementById("empty-state");
const elChipsContainer = document.getElementById("chips-container");
const elChatInput = document.getElementById("chat-input");
const elBtnSend = document.getElementById("btn-send");
const elBtnStop = document.getElementById("btn-stop");
const elBtnClearChat = document.getElementById("btn-clear-chat");
const elBtnOpenSettings = document.getElementById("btn-open-settings");
const elSettingsModal = document.getElementById("settings-modal");
const elBtnCloseSettings = document.getElementById("btn-close-settings");
const elBtnSaveSettings = document.getElementById("btn-save-settings");
const elSelectAnswerStyle = document.getElementById("select-answer-style");
const elSelectUiLanguage = document.getElementById("select-ui-language");

function showAlert(message) {
  if (!message) {
    elAlertBox.classList.add("hidden");
    elAlertBox.textContent = "";
    return;
  }
  elAlertBox.textContent = message;
  elAlertBox.classList.remove("hidden");
}

function clearAlert() {
  showAlert("");
}

function updateI18nLabels() {
  elAppTitle.textContent = t("app_title");
  elBtnAnalyzeText.textContent = state.pageId ? t("reanalyze") : t("analyze");
  elBtnSummary.textContent = t("summary");
  elBtnExplainSelection.textContent = t("explain_selection");
  elChatInput.placeholder = t("input_placeholder");
  elBtnSend.textContent = t("send");
  elBtnStop.textContent = t("stop");
  elBannerText.textContent = t("banner_page_changed");
  elBtnBannerReanalyze.textContent = t("analyze");
  elNoteTruncated.textContent = t("note_truncated");

  // Chips
  const chips = elChipsContainer.querySelectorAll(".chip-btn");
  if (chips[0]) chips[0].textContent = t("chip_1");
  if (chips[1]) chips[1].textContent = t("chip_2");
  if (chips[2]) chips[2].textContent = t("chip_3");
}

function renderAllMessages() {
  while (elChatContainer.firstChild) {
    elChatContainer.removeChild(elChatContainer.firstChild);
  }

  if (state.messages.length === 0) {
    elChatContainer.appendChild(elEmptyState);
    return;
  }

  state.messages.forEach((msg) => {
    const el = renderMessageElement(
      msg,
      (srcId) => {
        // Source chip clicked: highlight in page
        const src = msg.sources?.find((s) => s.id === srcId);
        if (src) {
          highlightInPage(state.tabId, src.text);
          const details = document.getElementById(`sources-details-${msg.id}`);
          if (details) details.open = true;
          const srcEl = document.getElementById(`source-${msg.id}-${srcId}`);
          if (srcEl) srcEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      },
      (text) => {
        // "View in page" button clicked
        highlightInPage(state.tabId, text);
      }
    );
    elChatContainer.appendChild(el);
  });

  scrollChatToBottom();
}

function scrollChatToBottom(force = false) {
  const isNearBottom =
    elChatContainer.scrollHeight - elChatContainer.scrollTop - elChatContainer.clientHeight < 120;
  if (force || isNearBottom) {
    elChatContainer.scrollTop = elChatContainer.scrollHeight;
  }
}

function updateUi() {
  updateI18nLabels();

  // Page title & info
  if (state.pageTitle) {
    elPageTitle.textContent = state.pageTitle;
  } else if (state.pageUrl) {
    elPageTitle.textContent = state.pageUrl;
  } else {
    elPageTitle.textContent = t("app_title");
  }

  // Chunks badge
  if (state.chunkCount > 0) {
    elBadgeChunks.textContent = `${state.chunkCount} chunks`;
    elBadgeChunks.classList.remove("hidden");
  } else {
    elBadgeChunks.classList.add("hidden");
  }

  // Truncated note
  if (state.truncated) {
    elNoteTruncated.classList.remove("hidden");
  } else {
    elNoteTruncated.classList.add("hidden");
  }

  // Banner
  if (state.status === "page_changed") {
    elBanner.classList.remove("hidden");
  } else {
    elBanner.classList.add("hidden");
  }

  // Status text
  if (state.status === "extracting") {
    elStatusText.textContent = t("extracting");
  } else if (state.status === "indexing") {
    elStatusText.textContent = t("indexing");
  } else if (state.status === "ready") {
    elStatusText.textContent = t("ready");
  } else {
    elStatusText.textContent = "";
  }

  // Buttons availability - never block the user from typing or asking!
  const isAnswering = state.status === "answering";
  const isAnalyzing = state.status === "extracting" || state.status === "indexing";

  elBtnAnalyze.disabled = isAnswering || isAnalyzing;
  elBtnSummary.disabled = isAnswering;
  elBtnExplainSelection.disabled = isAnswering;
  elChatInput.disabled = isAnswering;
  elBtnSend.disabled = isAnswering || !elChatInput.value.trim();

  if (state.status === "extracting") {
    elChatInput.placeholder = t("extracting");
  } else if (state.status === "indexing") {
    elChatInput.placeholder = t("indexing");
  } else {
    elChatInput.placeholder = t("input_placeholder");
  }

  // Streaming stop button
  if (state.status === "answering") {
    elBtnStop.classList.remove("hidden");
    elBtnSend.classList.add("hidden");
  } else {
    elBtnStop.classList.add("hidden");
    elBtnSend.classList.remove("hidden");
  }

  // Suggestion chips: always visible when chat is empty and not answering!
  if (!isAnswering && state.messages.length === 0) {
    elChipsContainer.classList.remove("hidden");
  } else {
    elChipsContainer.classList.add("hidden");
  }
}

async function handleAnalyze() {
  clearAlert();
  const tab = await getActiveTab();
  if (!tab || !tab.id) {
    showAlert(t("err_restricted"));
    return;
  }

  state.tabId = tab.id;
  state.pageUrl = tab.url ? tab.url.split("#")[0] : "";
  state.status = "extracting";
  updateUi();

  // 1. Extract page content
  const extractResult = await extractActivePage(tab.id, tab.url);
  if (!extractResult.ok) {
    state.status = "error";
    if (extractResult.reason === "login_page") {
      showAlert(t("err_login_page"));
    } else if (extractResult.reason === "restricted") {
      showAlert(t("err_restricted"));
    } else {
      showAlert(t("err_generic"));
    }
    updateUi();
    return;
  }

  if (!extractResult.text || extractResult.text.length < 100) {
    state.status = "error";
    showAlert(t("err_too_short"));
    updateUi();
    return;
  }

  state.pageTitle = extractResult.title || tab.title || "";
  state.extractedText = extractResult.text;
  state.truncated = extractResult.truncated;
  state.status = "indexing";
  updateUi();

  // 2. Index with backend
  const coldStartTimer = setTimeout(() => {
    if (state.status === "indexing") {
      elStatusText.textContent = t("server_waking");
    }
  }, 1800);

  try {
    const res = await indexPage(state.settings.backendUrl, {
      url: extractResult.url,
      title: state.pageTitle,
      text: extractResult.text,
      truncated: extractResult.truncated,
      lang: extractResult.lang || "en",
    });
    clearTimeout(coldStartTimer);

    state.pageId = res.page_id;
    state.chunkCount = res.chunk_count;
    state.truncated = res.truncated;
    state.status = "ready";
    state.saveCurrentTabSession();
    clearAlert();
  } catch (err) {
    clearTimeout(coldStartTimer);
    console.error("Index error:", err);
    state.status = "error";
    if (err.code === "BACKEND_DOWN") {
      showAlert(t("err_backend_down"));
    } else if (err.code === "LLM_QUOTA_EXCEEDED" || err.code === "RATE_LIMITED") {
      showAlert(t("err_quota"));
    } else if (err.code === "TEXT_TOO_SHORT") {
      showAlert(t("err_too_short"));
    } else {
      showAlert(err.messageBn || t("err_generic"));
    }
  }

  updateUi();
}

let activeAnalyzePromise = null;

async function ensurePageAnalyzed() {
  if (state.pageId) return true;
  if (activeAnalyzePromise) return await activeAnalyzePromise;

  activeAnalyzePromise = (async () => {
    try {
      await handleAnalyze();
      return Boolean(state.pageId);
    } catch (err) {
      console.warn("Auto-analyze error:", err);
      return false;
    } finally {
      activeAnalyzePromise = null;
    }
  })();

  return await activeAnalyzePromise;
}

/**
 * Common streaming runner with F-22 auto-recovery support.
 */
async function runStreamingTask(path, body, retryCount = 0) {
  clearAlert();
  const assistantMsgId = Date.now();
  const assistantMsg = {
    id: assistantMsgId,
    role: "assistant",
    text: "",
    sources: [],
    streaming: true,
    stopped: false,
  };

  state.messages.push(assistantMsg);
  state.status = "answering";
  updateUi();
  renderAllMessages();
  scrollChatToBottom(true);

  state.abortController = new AbortController();
  let rafId = null;
  let textBuffer = "";

  function scheduleRender() {
    if (rafId) return;
    rafId = requestAnimationFrame(() => {
      assistantMsg.text = textBuffer;
      const bubbleEl = document.getElementById(`msg-${assistantMsgId}`);
      if (bubbleEl) {
        const contentEl = bubbleEl.querySelector(".msg-content");
        if (contentEl) {
          renderMarkdownSubset(textBuffer, contentEl, assistantMsg.sources);
          if (assistantMsg.streaming) {
            const cursor = document.createElement("span");
            cursor.className = "streaming-cursor";
            cursor.textContent = "▍";
            contentEl.appendChild(cursor);
          }
        }
      }
      scrollChatToBottom();
      rafId = null;
    });
  }

  try {
    await streamPost(state.settings.backendUrl, path, body, {
      signal: state.abortController.signal,
      onEvent: (event) => {
        if (event.type === "sources") {
          assistantMsg.sources = event.sources || [];
        } else if (event.type === "token") {
          textBuffer += event.text;
          scheduleRender();
        } else if (event.type === "error") {
          assistantMsg.text += `\n\n⚠️ ${event.message_bn || t("err_generic")}`;
          scheduleRender();
        } else if (event.type === "done") {
          assistantMsg.streaming = false;
        }
      },
    });

    assistantMsg.text = textBuffer;
    assistantMsg.streaming = false;
    state.status = "ready";
    state.saveCurrentTabSession();
  } catch (err) {
    console.warn("Stream error:", err);
    assistantMsg.streaming = false;

    // F-22: Auto-recovery if PAGE_NOT_FOUND (server restarted or evicted)
    if (err.code === "PAGE_NOT_FOUND" && state.extractedText && retryCount === 0) {
      console.info("Index not found on server, attempting transparent re-indexing...");
      state.messages.pop(); // remove current failed assistant message
      try {
        const reindexRes = await indexPage(state.settings.backendUrl, {
          url: state.pageUrl,
          title: state.pageTitle,
          text: state.extractedText,
          truncated: state.truncated,
          lang: "en",
        });
        state.pageId = reindexRes.page_id;
        body.page_id = reindexRes.page_id;
        return await runStreamingTask(path, body, retryCount + 1);
      } catch (reindexErr) {
        showAlert(t("err_generic"));
      }
    } else {
      if (err.code === "BACKEND_DOWN") {
        showAlert(t("err_backend_down"));
      } else if (err.code === "LLM_QUOTA_EXCEEDED" || err.code === "RATE_LIMITED") {
        showAlert(t("err_quota"));
      } else {
        showAlert(err.messageBn || t("err_generic"));
      }
      state.status = "ready";
    }
  } finally {
    if (rafId) cancelAnimationFrame(rafId);
    assistantMsg.streaming = false;
    state.abortController = null;
    updateUi();
    renderAllMessages();
    scrollChatToBottom(true);
  }
}

async function handleSendMessage(customText = null) {
  const text = customText !== null ? customText : elChatInput.value.trim();
  if (!text || state.status === "answering") return;

  elChatInput.value = "";
  elChatInput.style.height = "auto";

  // Add user message immediately
  state.messages.push({
    id: Date.now(),
    role: "user",
    text,
    sources: [],
    streaming: false,
  });
  renderAllMessages();
  scrollChatToBottom(true);

  // If page not analyzed yet, auto-analyze on demand
  if (!state.pageId) {
    const ok = await ensurePageAnalyzed();
    if (!ok) return;
  }

  // Prepare history messages (up to 8)
  const history = state.messages
    .slice(0, -1)
    .filter((m) => m.role === "user" || m.role === "assistant")
    .slice(-8)
    .map((m) => ({
      role: m.role,
      content: m.text,
    }));

  await runStreamingTask("/api/v1/chat", {
    page_id: state.pageId,
    question: text,
    style: state.settings.answerStyle,
    history,
  });
}

async function handleSummary() {
  if (state.status === "answering") return;
  if (!state.pageId) {
    const ok = await ensurePageAnalyzed();
    if (!ok) return;
  }
  await runStreamingTask("/api/v1/summarize", {
    page_id: state.pageId,
    style: state.settings.answerStyle,
  });
}

async function handleExplainSelection() {
  if (state.status === "answering") return;
  clearAlert();

  const selection = await getSelectionFromPage(state.tabId);
  if (!selection) {
    showAlert(t("err_no_selection"));
    return;
  }

  if (!state.pageId) {
    const ok = await ensurePageAnalyzed();
    if (!ok) return;
  }

  await runStreamingTask("/api/v1/explain-selection", {
    page_id: state.pageId,
    selection,
    style: state.settings.answerStyle,
  });
}

function handleStop() {
  if (state.abortController) {
    state.abortController.abort();
    state.abortController = null;
  }
  const lastMsg = state.messages[state.messages.length - 1];
  if (lastMsg && lastMsg.role === "assistant" && lastMsg.streaming) {
    lastMsg.streaming = false;
    lastMsg.stopped = true;
  }
  state.status = "ready";
  updateUi();
  renderAllMessages();
}

function handleClearChat() {
  state.messages = [];
  state.saveCurrentTabSession();
  renderAllMessages();
  updateUi();
}

// Tab navigation tracking
async function checkCurrentTab() {
  const tab = await getActiveTab();
  if (!tab || !tab.id) return;

  const cleanUrl = tab.url ? tab.url.split("#")[0] : "";
  if (state.tabId === tab.id) {
    if (state.pageUrl && cleanUrl && state.pageUrl !== cleanUrl) {
      state.status = "page_changed";
      updateUi();
    }
  } else {
    state.saveCurrentTabSession();
    state.restoreTabSession(tab.id, cleanUrl);
    updateUi();
    renderAllMessages();
  }
}

// Auto-grow textarea
function autoGrowTextarea() {
  elChatInput.style.height = "auto";
  elChatInput.style.height = Math.min(elChatInput.scrollHeight, 120) + "px";
  elBtnSend.disabled = state.status !== "ready" || !elChatInput.value.trim();
}

// Settings modal
async function openSettings() {
  elSelectAnswerStyle.value = state.settings.answerStyle;
  elSelectUiLanguage.value = state.settings.uiLanguage;
  elSettingsModal.classList.remove("hidden");
}

async function closeSettings() {
  elSettingsModal.classList.add("hidden");
}

async function saveSettingsFromModal() {
  const newStyle = elSelectAnswerStyle.value;
  const newLang = elSelectUiLanguage.value;

  state.settings = await saveSettings({
    backendUrl: state.settings.backendUrl || "https://page-explainer-bangla.onrender.com",
    answerStyle: newStyle,
    uiLanguage: newLang,
  });

  setLanguage(newLang);
  closeSettings();
  updateUi();
}

// Event Listeners Initialization
function initEventListeners() {
  elBtnAnalyze.addEventListener("click", handleAnalyze);
  elBtnBannerReanalyze.addEventListener("click", handleAnalyze);
  elBtnSummary.addEventListener("click", handleSummary);
  elBtnExplainSelection.addEventListener("click", handleExplainSelection);
  elBtnSend.addEventListener("click", () => handleSendMessage());
  elBtnStop.addEventListener("click", handleStop);
  elBtnClearChat.addEventListener("click", handleClearChat);

  elChatInput.addEventListener("input", autoGrowTextarea);
  elChatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  // Suggestion chips
  elChipsContainer.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip-btn");
    if (chip) {
      handleSendMessage(chip.textContent.trim());
    }
  });

  // Settings
  elBtnOpenSettings.addEventListener("click", openSettings);
  elBtnCloseSettings.addEventListener("click", closeSettings);
  elBtnSaveSettings.addEventListener("click", saveSettingsFromModal);

  // Esc closes settings modal
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !elSettingsModal.classList.contains("hidden")) {
      closeSettings();
    }
  });

  // Tab activation and update listeners
  const tabsApi =
    typeof chrome !== "undefined" && chrome.tabs
      ? chrome.tabs
      : typeof browser !== "undefined" && browser.tabs
      ? browser.tabs
      : null;

  if (tabsApi) {
    tabsApi.onActivated.addListener(() => {
      checkCurrentTab();
    });
    tabsApi.onUpdated.addListener((tabId, changeInfo) => {
      if (changeInfo.url || changeInfo.status === "complete") {
        checkCurrentTab();
      }
    });
  }
}

// Bootstrapping
async function init() {
  state.settings = await loadSettings();
  setLanguage(state.settings.uiLanguage || "bn");

  initEventListeners();
  updateUi();
  renderAllMessages();

  await checkCurrentTab();

  // Background Pre-heat:
  // 1. Silently wake up Render backend if cold
  if (state.settings && state.settings.backendUrl) {
    fetch(`${state.settings.backendUrl}/health`).catch(() => {});
  }

  // 2. Silently extract and index active page in background so it's ready before user even asks
  if (!state.pageId) {
    ensurePageAnalyzed().catch(() => {});
  }
}

document.addEventListener("DOMContentLoaded", init);

