import { activityTypes, text } from "./labels.js";

const ACCENT = "#f2c318";
const ERROR = "#e5484d";
const DEFAULT_VIEW = { center: [-14.2, -51.9], zoom: 4 };
const PHOTO_ZOOM = 17;
const FLY_DURATION_SECONDS = 1.5;
const VISIT_STYLE = { radius: 9, color: ACCENT, fillColor: ACCENT, fillOpacity: 0.35, weight: 2 };
const BOUNDARY_STYLE = { radius: 5, color: ACCENT, fillColor: ACCENT, fillOpacity: 1, weight: 1 };

export function createMapPanel(container, emptyMessage) {
  const map = L.map(container, { zoomControl: false }).setView(DEFAULT_VIEW.center, DEFAULT_VIEW.zoom);
  const routeLayer = L.layerGroup();
  let routeBounds = null;
  let photoMarker = null;
  let viewToken = 0;

  map.attributionControl.setPrefix(false);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap",
  }).addTo(map);

  function drawTimeline(timeline) {
    const points = timeline?.points ?? [];
    if (points.length) {
      const latLngs = points.map((point) => [point.lat, point.lng]);
      L.polyline(latLngs, { color: ACCENT, weight: 3, dashArray: "6 8" }).addTo(routeLayer);
      timeline.activities.forEach(drawActivity);
      drawStops(timeline);
      routeBounds = L.latLngBounds(latLngs);
    }
    if (!photoMarker) {
      showRoute(false);
    }
  }

  function drawStops(timeline) {
    const visits = groupByPlace(
      timeline.visits.map((visit) => ({
        ...visit,
        label: `${text.visit} · ${formatTime(visit.startTime)}–${formatTime(visit.endTime)}`,
      })),
    );
    const boundaries = groupByPlace(
      timeline.activities.flatMap((activity) => {
        const type = activityTypes[activity.type] ?? text.unknownActivity;
        return [
          { ...activity.start, label: `${text.activityStart} · ${type} · ${formatTime(activity.startTime)}` },
          { ...activity.end, label: `${text.activityEnd} · ${type} · ${formatTime(activity.endTime)}` },
        ];
      }),
    );
    visits.forEach((place) => drawStop(place, VISIT_STYLE));
    boundaries.forEach((place, key) => {
      if (!visits.has(key)) {
        drawStop(place, BOUNDARY_STYLE);
      }
    });
  }

  function drawStop(place, style) {
    L.circleMarker([place.lat, place.lng], style)
      .bindPopup(createPopupContent(place.labels))
      .addTo(routeLayer);
  }

  function drawActivity(activity) {
    const label = activityTypes[activity.type] ?? text.unknownActivity;
    const distance = activity.distanceMeters != null ? ` · ${formatKilometers(activity.distanceMeters)}` : "";
    L.polyline(
      [
        [activity.start.lat, activity.start.lng],
        [activity.end.lat, activity.end.lng],
      ],
      { color: ACCENT, opacity: 0, weight: 16 },
    )
      .bindPopup(`${label}${distance}`)
      .addTo(routeLayer);
  }

  function showRoute(animate = true) {
    clearLayers();
    emptyMessage.hidden = Boolean(routeBounds);
    if (!routeBounds) {
      return;
    }
    const options = { padding: [24, 24], maxZoom: PHOTO_ZOOM, duration: FLY_DURATION_SECONDS };
    showAfterMove(routeLayer, () =>
      animate ? map.flyToBounds(routeBounds, options) : map.fitBounds(routeBounds, { ...options, animate: false }),
    );
  }

  function showPhoto({ lat, lng }) {
    clearLayers();
    emptyMessage.hidden = true;
    photoMarker = L.circleMarker([lat, lng], {
      radius: 8,
      color: ERROR,
      fillColor: ERROR,
      fillOpacity: 1,
      weight: 2,
    });
    showAfterMove(photoMarker, () => map.flyTo([lat, lng], PHOTO_ZOOM, { duration: FLY_DURATION_SECONDS }));
  }

  function clearLayers() {
    map.closePopup();
    routeLayer.remove();
    photoMarker?.remove();
  }

  function showAfterMove(layer, move) {
    const token = ++viewToken;
    map.once("moveend", () => {
      if (token === viewToken) {
        layer.addTo(map);
      }
    });
    move();
  }

  function apply(state) {
    if (state.action === "route") {
      showRoute(true);
    } else if (state.action === "photo") {
      showPhoto(state);
    }
  }

  return { drawTimeline, apply };
}

function groupByPlace(items) {
  const places = new Map();
  for (const item of items) {
    const key = `${item.lat.toFixed(4)},${item.lng.toFixed(4)}`;
    const place = places.get(key) ?? { lat: item.lat, lng: item.lng, labels: [] };
    if (!place.labels.includes(item.label)) {
      place.labels.push(item.label);
    }
    places.set(key, place);
  }
  return places;
}

function createPopupContent(lines) {
  const content = document.createElement("div");
  lines.forEach((line, index) => {
    if (index) {
      content.append(document.createElement("br"));
    }
    content.append(line);
  });
  return content;
}

function formatTime(isoDate) {
  return isoDate ? isoDate.slice(11, 16) : text.notAvailable;
}

function formatKilometers(meters) {
  return `${(meters / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} km`;
}
