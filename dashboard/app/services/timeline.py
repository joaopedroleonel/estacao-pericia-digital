from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.utils import parse_degree_pair


@dataclass
class TimelinePoint:
    lat: float
    lng: float
    time: datetime

    def to_dict(self) -> dict:
        return {"lat": self.lat, "lng": self.lng, "time": self.time.isoformat()}


@dataclass
class TimelineVisit:
    lat: float
    lng: float
    start_time: datetime
    end_time: datetime | None

    def to_dict(self) -> dict:
        return {
            "lat": self.lat,
            "lng": self.lng,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat() if self.end_time else None,
        }


@dataclass
class TimelineActivity:
    start: tuple[float, float]
    end: tuple[float, float]
    start_time: datetime
    end_time: datetime | None
    distance_meters: float | None
    activity_type: str | None

    def to_dict(self) -> dict:
        return {
            "start": {"lat": self.start[0], "lng": self.start[1]},
            "end": {"lat": self.end[0], "lng": self.end[1]},
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "distanceMeters": self.distance_meters,
            "type": self.activity_type,
        }


@dataclass
class Timeline:
    points: list[TimelinePoint] = field(default_factory=list)
    visits: list[TimelineVisit] = field(default_factory=list)
    activities: list[TimelineActivity] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.points

    def to_dict(self) -> dict:
        return {
            "points": [point.to_dict() for point in self.points],
            "visits": [visit.to_dict() for visit in self.visits],
            "activities": [activity.to_dict() for activity in self.activities],
        }


def load_timeline(path: Path, day: str = "") -> Timeline:
    with path.open(encoding="utf-8") as file:
        return parse_timeline(json.load(file), day)


def parse_timeline(data: object, day: str = "") -> Timeline:
    timeline = Timeline()
    segments = data.get("semanticSegments", []) if isinstance(data, dict) else []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        start_time = _parse_time(segment.get("startTime"))
        if start_time is None or (day and start_time.date().isoformat() != day):
            continue
        end_time = _parse_time(segment.get("endTime"))
        _add_path(timeline, segment.get("timelinePath"))
        _add_visit(timeline, segment.get("visit"), start_time, end_time)
        _add_activity(timeline, segment.get("activity"), start_time, end_time)
    timeline.points = _merge_repeated(sorted(timeline.points, key=lambda point: point.time))
    timeline.visits.sort(key=lambda visit: visit.start_time)
    timeline.activities.sort(key=lambda activity: activity.start_time)
    return timeline


def _add_path(timeline: Timeline, path: object) -> None:
    if not isinstance(path, list):
        return
    for item in path:
        if not isinstance(item, dict):
            continue
        coordinates = parse_degree_pair(item.get("point"))
        time = _parse_time(item.get("time"))
        if coordinates and time:
            timeline.points.append(TimelinePoint(*coordinates, time))


def _add_visit(timeline: Timeline, visit: object, start_time: datetime, end_time: datetime | None) -> None:
    if not isinstance(visit, dict):
        return
    location = _dig(visit, "topCandidate", "placeLocation", "latLng")
    coordinates = parse_degree_pair(location)
    if coordinates:
        timeline.visits.append(TimelineVisit(*coordinates, start_time, end_time))
        timeline.points.append(TimelinePoint(*coordinates, start_time))


def _add_activity(timeline: Timeline, activity: object, start_time: datetime, end_time: datetime | None) -> None:
    if not isinstance(activity, dict):
        return
    start = parse_degree_pair(_dig(activity, "start", "latLng"))
    end = parse_degree_pair(_dig(activity, "end", "latLng"))
    if not start or not end:
        return
    distance = activity.get("distanceMeters")
    timeline.activities.append(
        TimelineActivity(
            start=start,
            end=end,
            start_time=start_time,
            end_time=end_time,
            distance_meters=float(distance) if isinstance(distance, (int, float)) else None,
            activity_type=_dig(activity, "topCandidate", "type"),
        )
    )
    timeline.points.append(TimelinePoint(*start, start_time))
    timeline.points.append(TimelinePoint(*end, end_time or start_time))


def _merge_repeated(points: list[TimelinePoint]) -> list[TimelinePoint]:
    merged: list[TimelinePoint] = []
    for point in points:
        if not merged or (merged[-1].lat, merged[-1].lng) != (point.lat, point.lng):
            merged.append(point)
    return merged


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _dig(data: dict, *keys: str) -> object:
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data
