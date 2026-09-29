import { text, uploadErrors } from "./labels.js";

const input = document.querySelector("#photo-input");
const status = document.querySelector("#upload-status");
const tokenQuery = `?token=${encodeURIComponent(new URLSearchParams(window.location.search).get("token") ?? "")}`;

input.addEventListener("change", async () => {
  const [photo] = input.files;
  if (!photo) {
    return;
  }
  setStatus(text.uploadSending, "");
  try {
    await uploadPhoto(photo);
    setStatus(text.uploadDone, "is-success");
  } catch (error) {
    setStatus(uploadErrors[error.message] ?? uploadErrors.request_failed, "is-error");
  } finally {
    input.value = "";
  }
});

async function uploadPhoto(photo) {
  const { uploadId, uploadUrl } = await postJson(`/api/uploads${tokenQuery}`);
  const upload = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": photo.type || "application/octet-stream" },
    body: photo,
  });
  if (!upload.ok) {
    const detail = await upload.text().catch(() => "");
    throw new Error(upload.status === 413 || /too large|413/i.test(detail) ? "too_large" : "request_failed");
  }
  await postJson(`/api/uploads/${uploadId}/confirm${tokenQuery}`);
}

async function postJson(url) {
  const response = await fetch(url, { method: "POST" });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(result.error ?? "request_failed");
  }
  return result;
}

function setStatus(message, className) {
  status.textContent = message;
  status.className = `upload-status ${className}`.trim();
}
