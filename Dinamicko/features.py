import math
import statistics
import string

from config import MIN_CHARS, MAX_INTERVAL_SECONDS


FEATURE_NAMES = [
    "hold_mean",
    "hold_std",
    "hold_median",
    "hold_min",
    "hold_max",

    "pp_mean",
    "pp_std",
    "pp_median",
    "pp_min",
    "pp_max",

    "rp_mean",
    "rp_std",
    "rp_median",
    "rp_min",
    "rp_max",

    "chars_per_second",
    "keys_per_second",
    "backspace_rate",
    "space_rate",
    "uppercase_rate",
    "digit_rate",
    "punctuation_rate",
    "enter_rate",
    "modifier_rate",
]


MODIFIER_KEYS = {
    "Shift",
    "ShiftLeft",
    "ShiftRight",
    "Control",
    "ControlLeft",
    "ControlRight",
    "Alt",
    "AltLeft",
    "AltRight",
    "Meta",
    "MetaLeft",
    "MetaRight",
    "CapsLock",
    "Tab",
}


def safe_float(value, default=0.0):
    try:
        result = float(value)

        if math.isfinite(result):
            return result

        return default
    except Exception:
        return default


def stats(values):
    if not values:
        return [0.0, 0.0, 0.0, 0.0, 0.0]

    values = list(values)

    mean = statistics.mean(values)

    if len(values) > 1:
        std = statistics.pstdev(values)
    else:
        std = 0.0

    median = statistics.median(values)
    minimum = min(values)
    maximum = max(values)

    return [
        float(mean),
        float(std),
        float(median),
        float(minimum),
        float(maximum),
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
        key = str(event.get("key", ""))
        code = str(event.get("code", ""))
        press = safe_float(event.get("press"))
        release = safe_float(event.get("release"))

        if release <= press:
            continue

        cleaned.append({
            "key": key,
            "code": code,
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

    usable_events = [
        event for event in events
        if not is_modifier(event["key"])
    ]

    if len(usable_events) < MIN_CHARS // 2:
        raise ValueError("Not enough usable key events were recorded.")

    hold_times = []
    press_press_times = []
    release_press_times = []

    for event in usable_events:
        hold_times.append(event["release"] - event["press"])

    for index in range(len(usable_events) - 1):
        current_event = usable_events[index]
        next_event = usable_events[index + 1]

        pp = next_event["press"] - current_event["press"]
        rp = next_event["press"] - current_event["release"]

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

    feature_vector = []

    feature_vector.extend(stats(hold_times))
    feature_vector.extend(stats(press_press_times))
    feature_vector.extend(stats(release_press_times))

    feature_vector.extend([
        float(char_count / duration),
        float(key_count / duration),
        float(backspace_count / char_count),
        float(space_count / char_count),
        float(uppercase_count / char_count),
        float(digit_count / char_count),
        float(punctuation_count / char_count),
        float(enter_count / char_count),
        float(modifier_count / key_count),
    ])

    return feature_vector