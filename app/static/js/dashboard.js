import { requestJson } from "./api.js";
import { createImagePanel } from "./image-panel.js";
import { createMapPanel } from "./map-panel.js";
import { createTerminal } from "./terminal.js";

const imagePanel = createImagePanel(document.querySelector("#image-panel"));
const mapPanel = createMapPanel(document.querySelector("#map"), document.querySelector("#map-empty"));

createTerminal(document.querySelector("#terminal"), applyState);

requestJson("/api/timeline")
  .then(mapPanel.drawTimeline)
  .catch(() => mapPanel.drawTimeline(null));

function applyState(state) {
  if (state.image) {
    imagePanel.show(state.image);
  }
  if (state.map) {
    mapPanel.apply(state.map);
  }
}
