import { formatBinary, summaryLabels, tagGroups, text } from "./labels.js";

const SUMMARY_FIELDS = Object.keys(summaryLabels);

export function createImagePanel(root) {
  const preview = root.querySelector(".image-preview");
  const placeholder = root.querySelector(".image-placeholder");
  const details = root.querySelector(".image-details");
  const summaryList = root.querySelector(".image-summary");
  const tagList = root.querySelector(".image-tags");

  renderSummary(summaryList, {});
  renderTags(tagList, []);

  function show(image) {
    preview.src = image.previewUrl;
    preview.hidden = false;
    placeholder.setAttribute("hidden", "");
    renderSummary(summaryList, image.summary);
    renderTags(tagList, image.tags);
    details.scrollTop = 0;
  }

  return { show };
}

function renderSummary(list, summary) {
  const rows = SUMMARY_FIELDS.flatMap((field) => {
    const value = formatSummaryValue(field, summary);
    const highlight = field === "gps" && value ? "is-highlight" : "";
    return createRow(summaryLabels[field], value ?? text.notAvailable, highlight);
  });
  list.replaceChildren(...rows);
}

function renderTags(list, tags) {
  const rows = [];
  let currentGroup = null;
  for (const tag of tags) {
    if (tag.group !== currentGroup) {
      currentGroup = tag.group;
      rows.push(createGroupTitle(tagGroups[currentGroup] ?? currentGroup));
    }
    rows.push(...createRow(tag.name, tag.value ?? formatBinary(tag.bytes)));
  }
  list.replaceChildren(...rows);
  list.hidden = rows.length === 0;
}

function formatSummaryValue(field, summary) {
  switch (field) {
    case "takenAt":
      return summary.takenAt ? formatDate(summary.takenAt) : null;
    case "gps":
      return summary.gps ? `${summary.gps.lat.toFixed(5)}, ${summary.gps.lng.toFixed(5)}` : null;
    case "resolution":
      return summary.width ? `${summary.width} x ${summary.height}` : null;
    case "altitude":
      return summary.altitude != null ? `${summary.altitude} m` : null;
    case "fileSize":
      return summary.fileSize != null ? formatBytes(summary.fileSize) : null;
    default:
      return summary[field] ?? null;
  }
}

function formatDate(isoDate) {
  const [date, time] = isoDate.split("T");
  const [year, month, day] = date.split("-");
  return `${day}/${month}/${year} ${time.slice(0, 5)}`;
}

function formatBytes(size) {
  const megabytes = size / 1024 / 1024;
  const [value, unit] = megabytes < 1 ? [size / 1024, "KB"] : [megabytes, "MB"];
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} ${unit}`;
}

function createRow(label, value, className = "") {
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value;
  description.className = className;
  return [term, description];
}

function createGroupTitle(label) {
  const title = document.createElement("dt");
  title.className = "image-tags-group";
  title.textContent = label;
  return title;
}
