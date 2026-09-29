from pathlib import Path

from app.services.timeline import load_timeline, parse_timeline


SAMPLE = Path(__file__).parent / "fixtures" / "timeline_sample.json"


def test_parses_path_visit_and_activity():
    timeline = load_timeline(SAMPLE, "2026-09-24")
    assert [(point.lat, point.lng) for point in timeline.points] == [
        (-24.5561, -54.0571),
        (-24.5583, -54.0549),
        (-24.5602, -54.061),
        (-24.553, -54.048),
    ]
    assert len(timeline.visits) == 1
    assert len(timeline.activities) == 1
    assert timeline.activities[0].distance_meters == 1850.4
    assert timeline.activities[0].activity_type == "IN_PASSENGER_VEHICLE"


def test_points_are_in_chronological_order():
    times = [point.time for point in load_timeline(SAMPLE, "2026-09-24").points]
    assert times == sorted(times)


def test_filters_by_day():
    assert load_timeline(SAMPLE, "2026-09-25").is_empty
    assert not load_timeline(SAMPLE).is_empty


def test_ignores_malformed_segments():
    data = {
        "semanticSegments": [
            None,
            {"startTime": "not a date"},
            {"startTime": "2026-09-24T08:00:00Z", "timelinePath": [{"point": "invalid", "time": "2026-09-24T08:00:00Z"}]},
            {"startTime": "2026-09-24T09:00:00Z", "visit": {"topCandidate": {}}},
        ]
    }
    assert parse_timeline(data).is_empty
    assert parse_timeline([]).is_empty


def test_serializes_to_api_format():
    payload = load_timeline(SAMPLE, "2026-09-24").to_dict()
    assert payload["points"][0] == {"lat": -24.5561, "lng": -54.0571, "time": "2026-09-24T08:02:00-03:00"}
    assert payload["visits"][0]["endTime"] == "2026-09-24T12:00:00-03:00"
    assert payload["activities"][0]["start"] == {"lat": -24.5602, "lng": -54.061}
