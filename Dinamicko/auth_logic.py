import math
import statistics
from datetime import datetime

from config import DISTANCE_THRESHOLD, MIN_SCALE
from features import FEATURE_NAMES, extract_features


def average_vectors(vectors):
    size = len(vectors[0])
    result = []

    for index in range(size):
        values = [vector[index] for vector in vectors]
        result.append(float(statistics.mean(values)))

    return result


def scale_vectors(vectors):
    size = len(vectors[0])
    result = []

    for index in range(size):
        values = [vector[index] for vector in vectors]

        if len(values) > 1:
            std = statistics.pstdev(values)
        else:
            std = 0.0

        result.append(float(max(std, MIN_SCALE)))

    return result


def create_user_profile(samples):
    vectors = [extract_features(sample) for sample in samples]

    profile = average_vectors(vectors)
    scale = scale_vectors(vectors)

    return {
        "type": "dynamic_free_text",
        "profile": profile,
        "scale": scale,
        "feature_names": FEATURE_NAMES,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "sample_count": len(samples),
    }


def calculate_distance(profile, scale, current_vector):
    total = 0.0
    count = len(profile)

    for index in range(count):
        normalized_difference = (current_vector[index] - profile[index]) / scale[index]
        total += normalized_difference ** 2

    return math.sqrt(total / count)


def check_login(user_profile, sample):
    current_vector = extract_features(sample)

    distance = calculate_distance(
        user_profile["profile"],
        user_profile["scale"],
        current_vector
    )

    approved = distance < DISTANCE_THRESHOLD

    return {
        "approved": approved,
        "distance": round(distance, 4),
        "threshold": DISTANCE_THRESHOLD,
    }