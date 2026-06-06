from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"

REGISTRATION_SAMPLES = 3
MIN_CHARS = 80

# Bigger value = easier login
# Smaller value = stricter login
DISTANCE_THRESHOLD = 1.0

MIN_SCALE = 0.03
MAX_INTERVAL_SECONDS = 4.0