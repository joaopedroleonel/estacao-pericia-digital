import { requestJson } from "./api.js";
import { loadingMessages, text } from "./labels.js";

const PROMPT = "perito@liaf:~$";
const SPINNER_FRAMES = ["|", "/", "-", "\\"];
const SPINNER_INTERVAL_MS = 100;
const MIN_LOADING_MS = 700;

export function createTerminal(root, onState) {
  const output = root.querySelector(".terminal-output");
  const form = root.querySelector(".terminal-line");
  const input = root.querySelector(".terminal-input");
  const history = [];
  let historyIndex = 0;

  root.addEventListener("click", () => input.focus());
  input.addEventListener("keydown", navigateHistory);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const command = input.value.trim();
    input.value = "";
    appendEcho(command);
    if (!command) {
      return;
    }
    remember(command);
    if (command === "clear") {
      output.replaceChildren();
      return;
    }
    await sendCommand(command);
  });

  async function sendCommand(command) {
    form.hidden = true;
    const loader = startLoader(loadingMessages[command.split(/\s+/)[0]]);
    const response = await fetchResponse(command, loader ? MIN_LOADING_MS : 0);
    loader?.stop();
    if (response) {
      response.output.forEach((line) => appendLine(line.text, line.style));
      onState(response.state);
    } else {
      appendLine(text.requestFailed, "error");
    }
    form.hidden = false;
    input.focus();
  }

  async function fetchResponse(command, minimumMs) {
    const request = requestJson("/api/terminal", { method: "POST", body: { command } });
    try {
      const [response] = await Promise.all([request, delay(minimumMs)]);
      return response;
    } catch {
      return null;
    }
  }

  function startLoader(message) {
    if (!message) {
      return null;
    }
    const line = document.createElement("div");
    const spinner = document.createElement("span");
    let frame = 0;
    line.className = "line-muted";
    spinner.className = "terminal-spinner";
    line.append(spinner, ` ${message}`);
    appendElement(line);
    const render = () => {
      spinner.textContent = SPINNER_FRAMES[frame % SPINNER_FRAMES.length];
      frame += 1;
    };
    render();
    const timer = setInterval(render, SPINNER_INTERVAL_MS);
    return {
      stop() {
        clearInterval(timer);
        line.remove();
      },
    };
  }

  function remember(command) {
    if (history.at(-1) !== command) {
      history.push(command);
    }
    historyIndex = history.length;
  }

  function navigateHistory(event) {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") {
      return;
    }
    event.preventDefault();
    const step = event.key === "ArrowUp" ? -1 : 1;
    historyIndex = Math.min(Math.max(historyIndex + step, 0), history.length);
    input.value = history[historyIndex] ?? "";
  }

  function appendEcho(command) {
    const line = document.createElement("div");
    const prompt = document.createElement("span");
    prompt.className = "terminal-prompt";
    prompt.textContent = PROMPT;
    line.className = "line-text";
    line.append(prompt, ` ${command}`);
    appendElement(line);
  }

  function appendLine(content, style) {
    const line = document.createElement("div");
    line.className = `line-${style}`;
    line.textContent = content;
    appendElement(line);
  }

  function appendElement(element) {
    output.append(element);
    output.scrollTop = output.scrollHeight;
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
