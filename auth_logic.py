import math
import statistics
from datetime import datetime

from config import DISTANCE_THRESHOLD, MIN_SCALE
from features import FEATURE_NAMES, extract_features


def average_vectors(vectors):
    return [float(statistics.mean(col)) for col in zip(*vectors)]


def scale_vectors(vectors):
    return [
        float(max(statistics.pstdev(col) if len(vectors) > 1 else 0.0, MIN_SCALE))
        for col in zip(*vectors)
    ]


def create_user_profile(samples):
    vectors = [extract_features(sample) for sample in samples]

    return {
        "type": "dynamic_free_text",
        "profile": average_vectors(vectors),
        "scale": scale_vectors(vectors),
        "feature_names": FEATURE_NAMES,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "sample_count": len(samples),
    }


def calculate_distance(profile, scale, current_vector):
    n = len(profile)
    total = sum(((v - p) / s) ** 2 for v, p, s in zip(current_vector, profile, scale))
    return math.sqrt(total / n)


def check_login(user_profile, sample):
    current_vector = extract_features(sample)

    distance = calculate_distance(
        user_profile["profile"],
        user_profile["scale"],
        current_vector,
    )

    approved = distance < DISTANCE_THRESHOLD

    return {
        "approved": approved,
        "distance": round(distance, 4),
        "threshold": DISTANCE_THRESHOLD,
    }
