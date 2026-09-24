// sidepanel/i18n.js
// Exact string dictionary from PRD §8.3

export const STRINGS = {
  bn: {
    app_title: "বাংলা পেজ এক্সপ্লেইনার",
    analyze: "এই পেজ বিশ্লেষণ করুন",
    reanalyze: "আবার বিশ্লেষণ করুন",
    extracting: "পেজ পড়া হচ্ছে…",
    indexing: "বুঝে নেওয়া হচ্ছে…",
    ready: "প্রস্তুত! এখন প্রশ্ন করুন",
    summary: "সারসংক্ষেপ",
    explain_selection: "নির্বাচিত অংশ বুঝিয়ে দিন",
    input_placeholder: "এই পেজ সম্পর্কে প্রশ্ন করুন…",
    send: "পাঠান",
    stop: "থামান",
    clear_chat: "চ্যাট মুছুন",
    copy: "কপি",
    copied: "কপি হয়েছে",
    sources: "সূত্র",
    view_in_page: "পেজে দেখুন",
    settings: "সেটিংস",
    backend_url: "ব্যাকএন্ড ঠিকানা",
    answer_style: "উত্তরের ধরন",
    style_simple: "সহজ",
    style_detailed: "বিস্তারিত",
    ui_language: "ইন্টারফেসের ভাষা",
    chip_1: "এই পেজটা কী নিয়ে?",
    chip_2: "মূল পয়েন্টগুলো বলুন",
    chip_3: "সহজ একটা উদাহরণ দিন",
    err_restricted: "এই পেজ পড়া সম্ভব নয় (ব্রাউজারের বিশেষ পেজ)।",
    err_login_page: "এটি লগইন পেজ মনে হচ্ছে, তাই পড়া হয়নি।",
    err_too_short: "এই পেজে বিশ্লেষণ করার মতো যথেষ্ট লেখা নেই।",
    err_no_selection: "আগে পেজে কিছু লেখা সিলেক্ট করুন।",
    err_backend_down: "সার্ভারের সাথে সংযোগ হচ্ছে না। ব্যাকএন্ড চালু আছে কি না দেখুন।",
    err_quota: "AI-এর ব্যবহারের সীমা শেষ। কিছুক্ষণ পরে আবার চেষ্টা করুন।",
    err_generic: "কিছু একটা সমস্যা হয়েছে। আবার চেষ্টা করুন।",
    banner_page_changed: "আপনি নতুন পেজে গেছেন। আবার বিশ্লেষণ করুন।",
    note_truncated: "পেজটি অনেক বড়, প্রথম অংশ বিশ্লেষণ করা হয়েছে।",
    not_in_page: "এই পেজে এর উত্তর পাওয়া যায়নি।",
    privacy_notice: "পেজের মূল লেখা ব্যাকএন্ডের মাধ্যমে গুগল জেমিনাই (Gemini) এপিআইতে পাঠানো হয়।"
  },
  en: {
    app_title: "Bangla Page Explainer",
    analyze: "Analyze this page",
    reanalyze: "Analyze again",
    extracting: "Reading the page…",
    indexing: "Understanding the page…",
    ready: "Ready! Ask a question",
    summary: "Summary",
    explain_selection: "Explain selection",
    input_placeholder: "Ask about this page…",
    send: "Send",
    stop: "Stop",
    clear_chat: "Clear chat",
    copy: "Copy",
    copied: "Copied",
    sources: "Sources",
    view_in_page: "Show in page",
    settings: "Settings",
    backend_url: "Backend URL",
    answer_style: "Answer style",
    style_simple: "Simple",
    style_detailed: "Detailed",
    ui_language: "Interface language",
    chip_1: "What is this page about?",
    chip_2: "Tell me the key points",
    chip_3: "Give me a simple example",
    err_restricted: "This page can't be read (special browser page).",
    err_login_page: "This looks like a login page, so it was not read.",
    err_too_short: "Not enough readable text on this page.",
    err_no_selection: "Select some text on the page first.",
    err_backend_down: "Can't reach the server. Is the backend running?",
    err_quota: "AI usage limit reached. Try again shortly.",
    err_generic: "Something went wrong. Please try again.",
    banner_page_changed: "You moved to a new page. Analyze again.",
    note_truncated: "The page is long; only the first part was analyzed.",
    not_in_page: "The page doesn't answer this.",
    privacy_notice: "Page text is sent via the backend to Google's Gemini API."
  }
};

let currentLanguage = "bn";

export function setLanguage(lang) {
  if (lang === "bn" || lang === "en") {
    currentLanguage = lang;
  }
}

export function getLanguage() {
  return currentLanguage;
}

export function t(key) {
  const dict = STRINGS[currentLanguage] || STRINGS.bn;
  return dict[key] || STRINGS.bn[key] || key;
}
