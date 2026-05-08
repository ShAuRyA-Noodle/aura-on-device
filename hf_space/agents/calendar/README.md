# CalendarAgent

Per `technical_spec.md` §3.2.

Conflict detection on a sweep over interval-tree-friendly sorted events
(precision target 1.00, recall >= 0.95). Travel-aware leave-by alerts default
to a `local_heuristic` (`dist_km / mode_speed_km_h`) — production wires up the
Google Distance Matrix free tier on Android.

## Inputs

```json
{
  "tick_ts": "2026-05-07T07:45:00+05:30",
  "events_today": [{"id":"e_12","start":"...","end":"...","loc_coords":{"lat":..,"lon":..},"travel_min":22}],
  "user_loc": {"lat":..,"lon":..},
  "preferences": {"buffer_minutes":15}
}
```

`events_today[*].travel_min` is honoured directly when present (overrides the
heuristic), so production code that already calls Distance Matrix can pass
the answer in.

## Outputs

```json
{
  "next_event": {"id":"e_12","leave_by":"...","travel_min":22},
  "conflicts": [{"pair":["e_x","e_y"],"overlap_min":30}],
  "suggestions": [{"slot_start":"...","slot_end":"...","reason":"..."}],
  "leave_by_alert": {"event_id":"e_12","alert_at":"..."}
}
```

## Tools

| Name | Purpose |
|---|---|
| `detect_conflicts` | Returns overlapping pairs of events. |
| `suggest_slots` | First free gap (>= duration_min) after the conflict. |
| `auto_decline` | Drafts a polite decline (templated). |
| `travel_aware_alert` | leave-by = start - travel_min - buffer_min. |
| `parse_ics_attachment` | Single VEVENT or multi-VEVENT ICS payload parser. |

## Fixtures

| File | Purpose |
|---|---|
| `fixtures/conflict_3.json` | Three overlapping events (Anu / Manish / stand-up). |
| `fixtures/no_conflict.json` | Disjoint quiz + lunch — false-positive guard. |
| `fixtures/travel_aware.json` | Rohan's Monday Brief leave-by alert. |

## Run tests

```bash
pytest agents/calendar -q
```
