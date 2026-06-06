from flask import Flask, jsonify, render_template, request

from config import REGISTRATION_SAMPLES, MIN_CHARS, DISTANCE_THRESHOLD
from storage import load_users, save_users
from auth_logic import create_user_profile, check_login

app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        registration_samples=REGISTRATION_SAMPLES,
        min_chars=MIN_CHARS,
        threshold=DISTANCE_THRESHOLD
    )


@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True)

        username = data.get("username", "").strip()
        samples = data.get("samples", [])

        if not username:
            return jsonify({
                "ok": False,
                "message": "Username is required."
            }), 400

        if len(samples) < REGISTRATION_SAMPLES:
            return jsonify({
                "ok": False,
                "message": f"{REGISTRATION_SAMPLES} samples are required."
            }), 400

        profile = create_user_profile(samples[:REGISTRATION_SAMPLES])

        users = load_users()
        users[username] = profile
        save_users(users)

        return jsonify({
            "ok": True,
            "message": f"User '{username}' registered.",
            "feature_count": len(profile["profile"])
        })

    except Exception as error:
        return jsonify({
            "ok": False,
            "message": str(error)
        }), 400


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)

        username = data.get("username", "").strip()
        sample = data.get("sample", {})

        users = load_users()

        if username not in users:
            return jsonify({
                "ok": False,
                "message": "User not found. Register first."
            }), 404

        result = check_login(users[username], sample)

        return jsonify({
            "ok": True,
            "approved": result["approved"],
            "message": "ACCESS APPROVED" if result["approved"] else "ACCESS DENIED",
            "distance": result["distance"],
            "threshold": result["threshold"]
        })

    except Exception as error:
        return jsonify({
            "ok": False,
            "message": str(error)
        }), 400


@app.route("/api/users", methods=["GET"])
def list_users():
    users = load_users()

    return jsonify({
        "ok": True,
        "users": list(users.keys())
    })


if __name__ == "__main__":
    app.run(debug=True)