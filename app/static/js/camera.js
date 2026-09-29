import { text, uploadErrors } from "./labels.js";

const input = document.querySelector("#photo-input");
const status = document.querySelector("#upload-status");
const token = new URLSearchParams(window.location.search).get("token") ?? "";

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
  const body = new FormData();
  body.append("photo", photo);
  const response = await fetch(`/api/upload?token=${encodeURIComponent(token)}`, { method: "POST", body });
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    throw new Error(result.error ?? "request_failed");
  }
}

function setStatus(message, className) {
  status.textContent = message;
  status.className = `form-message ${className}`.trim();
}
