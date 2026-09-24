// sidepanel/api.js
import { normalizeBackendUrl } from "./settings.js";

export class ApiError extends Error {
  constructor(code, message, messageBn, httpStatus = 500) {
    super(message);
    this.code = code;
    this.messageBn = messageBn;
    this.httpStatus = httpStatus;
  }
}

export async function toApiError(response) {
  try {
    const data = await response.json();
    if (data && data.error) {
      return new ApiError(
        data.error.code || "INTERNAL_ERROR",
        data.error.message || "Request failed",
        data.error.message_bn || "",
        response.status
      );
    }
  } catch (e) {
    // Non-JSON response
  }
  return new ApiError(
    "INTERNAL_ERROR",
    `Server returned ${response.status} ${response.statusText}`,
    "",
    response.status
  );
}

export async function indexPage(backendUrl, payload) {
  const base = normalizeBackendUrl(backendUrl);
  try {
    const res = await fetch(`${base}/api/v1/pages/index`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw await toApiError(res);
    }
    return await res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new ApiError("BACKEND_DOWN", "Failed to reach server", "");
    }
    throw new ApiError("INTERNAL_ERROR", String(err), "");
  }
}

export async function streamPost(backendUrl, path, body, { onEvent, signal }) {
  const base = normalizeBackendUrl(backendUrl);
  let res;
  try {
    res = await fetch(`${base}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") {
      return; // User stopped streaming
    }
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new ApiError("BACKEND_DOWN", "Failed to reach server", "");
    }
    throw new ApiError("INTERNAL_ERROR", String(err), "");
  }

  if (!res.ok) {
    throw await toApiError(res);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let newlineIdx;
      while ((newlineIdx = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, newlineIdx).trim();
        buffer = buffer.slice(newlineIdx + 1);
        if (line) {
          try {
            const event = JSON.parse(line);
            onEvent(event);
          } catch (jsonErr) {
            console.warn("[Bangla Page Explainer] Error parsing NDJSON line:", line, jsonErr);
          }
        }
      }
    }
  } catch (readErr) {
    if (readErr.name === "AbortError") {
      return;
    }
    throw readErr;
  }
}
