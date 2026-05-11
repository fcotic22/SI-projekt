import math
import statistics
import string

from config import MIN_CHARS, MAX_INTERVAL_SECONDS


FEATURE_NAMES = [
    "hold_mean", "hold_std", "hold_median", "hold_min", "hold_max",
    "pp_mean", "pp_std", "pp_median", "pp_min", "pp_max",
    "rp_mean", "rp_std", "rp_median", "rp_min", "rp_max",
    "chars_per_second", "keys_per_second", "backspace_rate", "space_rate",
    "uppercase_rate", "digit_rate", "punctuation_rate", "enter_rate", "modifier_rate",
]


MODIFIER_KEYS = {
    "Shift", "ShiftLeft", "ShiftRight",
    "Control", "ControlLeft", "ControlRight",
    "Alt", "AltLeft", "AltRight",
    "Meta", "MetaLeft", "MetaRight",
    "CapsLock", "Tab",
}


def safe_float(value, default=0.0):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def stats(values):
    if not values:
        return [0.0, 0.0, 0.0, 0.0, 0.0]

    return [
        statistics.mean(values),
        statistics.pstdev(values) if len(values) > 1 else 0.0,
        statistics.median(values),
        min(values),
        max(values),
    ]


def is_modifier(key):
    return key in MODIFIER_KEYS


def is_backspace(key):
    return key == "Backspace"


def is_enter(key):
    return key == "Enter"


def clean_events(raw_events):
    cleaned = []

    for event in raw_events:
        press = safe_float(event.get("press"))
        release = safe_float(event.get("release"))

        if release <= press:
            continue

        cleaned.append({
            "key": str(event.get("key", "")),
            "code": str(event.get("code", "")),
            "press": press,
            "release": release,
        })

    cleaned.sort(key=lambda e: e["press"])
    return cleaned


def extract_features(sample):
    text = sample.get("typedText", "")
    events = clean_events(sample.get("events", []))

    if len(text) < MIN_CHARS:
        raise ValueError(f"Text is too short. Minimum is {MIN_CHARS} characters.")

    if len(events) < MIN_CHARS // 2:
        raise ValueError("Not enough key events were recorded.")

    usable_events = [e for e in events if not is_modifier(e["key"])]

    if len(usable_events) < MIN_CHARS // 2:
        raise ValueError("Not enough usable key events were recorded.")

    hold_times = [e["release"] - e["press"] for e in usable_events]

    press_press_times = []
    release_press_times = []

    for cur, nxt in zip(usable_events, usable_events[1:]):
        pp = nxt["press"] - cur["press"]
        rp = nxt["press"] - cur["release"]

        if 0 <= pp <= MAX_INTERVAL_SECONDS:
            press_press_times.append(pp)

        if -0.3 <= rp <= MAX_INTERVAL_SECONDS:
            release_press_times.append(rp)

    first_press = usable_events[0]["press"]
    last_release = usable_events[-1]["release"]
    duration = max(last_release - first_press, 0.001)

    char_count = max(len(text), 1)
    key_count = max(len(usable_events), 1)

    backspace_count = sum(1 for e in usable_events if is_backspace(e["key"]))
    enter_count = sum(1 for e in usable_events if is_enter(e["key"]))
    modifier_count = sum(1 for e in events if is_modifier(e["key"]))

    space_count = sum(1 for ch in text if ch.isspace())
    uppercase_count = sum(1 for ch in text if ch.isupper())
    digit_count = sum(1 for ch in text if ch.isdigit())
    punctuation_count = sum(1 for ch in text if ch in string.punctuation)

    return [
        *stats(hold_times),
        *stats(press_press_times),
        *stats(release_press_times),
        char_count / duration,
        key_count / duration,
        backspace_count / char_count,
        space_count / char_count,
        uppercase_count / char_count,
        digit_count / char_count,
        punctuation_count / char_count,
        enter_count / char_count,
        modifier_count / key_count,
    ]
