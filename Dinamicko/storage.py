import json
from config import DATA_DIR, USERS_FILE


def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)

    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")


def load_users():
    ensure_storage()

    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_users(users):
    ensure_storage()

    USERS_FILE.write_text(
        json.dumps(users, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )