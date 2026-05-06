from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "datasetStaticka" / "DSL-StrongPasswordData.csv"
MODEL_FILE = BASE_DIR / "keystroke_model.joblib"
USERS_FILE = BASE_DIR / "korisnici_profili.json"

KLJUCNA_RIJEC = ".tie5Roanl"
BROJ_PONAVLJANJA = 3
PRAG_UDALJENOSTI = 0.8

TIPKE = ["period", "t", "i", "e", "five", "Shift.r", "o", "a", "n", "l", "Return"]
FEATURE_COLUMNS = [
    "H.period", "DD.period.t", "UD.period.t",
    "H.t", "DD.t.i", "UD.t.i",
    "H.i", "DD.i.e", "UD.i.e",
    "H.e", "DD.e.five", "UD.e.five",
    "H.five", "DD.five.Shift.r", "UD.five.Shift.r",
    "H.Shift.r", "DD.Shift.r.o", "UD.Shift.r.o",
    "H.o", "DD.o.a", "UD.o.a",
    "H.a", "DD.a.n", "UD.a.n",
    "H.n", "DD.n.l", "UD.n.l",
    "H.l", "DD.l.Return", "UD.l.Return",
    "H.Return"
]

app = Flask(__name__, static_folder="assets", static_url_path="/assets")
model_bundle = None


def ucitaj_korisnike():
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        USERS_FILE.write_text("{}", encoding="utf-8")
        return {}


def spremi_korisnike(korisnici):
    USERS_FILE.write_text(json.dumps(korisnici, indent=2, ensure_ascii=False), encoding="utf-8")


def inicijaliziraj_model():
    global model_bundle
    if MODEL_FILE.exists():
        model_bundle = joblib.load(MODEL_FILE)
        return
    if not DATASET_PATH.exists():
        model_bundle = None
        return
    df = pd.read_csv(DATASET_PATH)
    X = df[FEATURE_COLUMNS].astype(float)
    le = LabelEncoder()
    y = le.fit_transform(df["subject"])
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    model_bundle = {"model": model, "classes": le.classes_.tolist(), "features": FEATURE_COLUMNS}
    joblib.dump(model_bundle, MODEL_FILE)


def izdvoji_znacajke(uzorak):
    tekst = uzorak.get("typedText", "")
    if tekst != KLJUCNA_RIJEC:
        raise ValueError(f"Unesena riječ nije ispravna: '{tekst}'")

    dogadaji = uzorak.get("events", [])
    po_tipki = {}

    for dogadaj in dogadaji:
        tipka = dogadaj.get("key")
        if tipka not in TIPKE or tipka in po_tipki:
            continue
        press = float(dogadaj.get("press"))
        release = float(dogadaj.get("release"))
        if release <= press:
            raise ValueError(f"Neispravno vrijeme za tipku {tipka}")
        po_tipki[tipka] = {"press": press, "release": release}

    nedostaje = [tipka for tipka in TIPKE if tipka not in po_tipki]
    if nedostaje:
        raise ValueError("Nedostaju događaji za: " + ", ".join(nedostaje))

    vremena = []
    for i, tipka in enumerate(TIPKE):
        trenutna = po_tipki[tipka]
        vremena.append(trenutna["release"] - trenutna["press"])
        if i < len(TIPKE) - 1:
            sljedeca = po_tipki[TIPKE[i + 1]]
            vremena.append(sljedeca["press"] - trenutna["press"])
            vremena.append(sljedeca["press"] - trenutna["release"])

    return np.array(vremena, dtype=float)


def dohvati_profil(vrijednost):
    if isinstance(vrijednost, dict):
        return np.array(vrijednost["profil"], dtype=float)
    return np.array(vrijednost, dtype=float)


@app.route("/")
def index():
    return render_template("index.html", kljucna_rijec=KLJUCNA_RIJEC, broj_ponavljanja=BROJ_PONAVLJANJA)


@app.route("/api/status")
def status():
    korisnici = ucitaj_korisnike()
    return jsonify({
        "model": MODEL_FILE.exists(),
        "dataset": DATASET_PATH.exists(),
        "korisnici": list(korisnici.keys()),
        "kljucnaRijec": KLJUCNA_RIJEC,
        "brojPonavljanja": BROJ_PONAVLJANJA,
        "prag": PRAG_UDALJENOSTI
    })


@app.route("/api/register", methods=["POST"])
def registracija():
    data = request.get_json(force=True)
    ime = data.get("ime", "").strip()
    uzorci = data.get("samples", [])
    overwrite = bool(data.get("overwrite", False))

    if not ime:
        return jsonify({"ok": False, "poruka": "Unesite ime korisnika."}), 400
    if len(uzorci) < BROJ_PONAVLJANJA:
        return jsonify({"ok": False, "poruka": f"Potrebna su {BROJ_PONAVLJANJA} uzorka."}), 400

    korisnici = ucitaj_korisnike()
    if ime in korisnici and not overwrite:
        return jsonify({"ok": False, "poruka": "Korisnik već postoji."}), 409

    try:
        vektori = [izdvoji_znacajke(uzorak) for uzorak in uzorci[:BROJ_PONAVLJANJA]]
    except ValueError as greska:
        return jsonify({"ok": False, "poruka": str(greska)}), 400

    profil = np.mean(vektori, axis=0)
    korisnici[ime] = {
        "profil": profil.tolist(),
        "broj_uzoraka": BROJ_PONAVLJANJA,
        "kljucna_rijec": KLJUCNA_RIJEC,
        "vrijeme_spremanja": datetime.now().isoformat(timespec="seconds")
    }
    spremi_korisnike(korisnici)

    return jsonify({"ok": True, "poruka": f"Korisnik '{ime}' je registriran.", "ime": ime})


@app.route("/api/login", methods=["POST"])
def prijava():
    data = request.get_json(force=True)
    ime = data.get("ime", "").strip()
    uzorak = data.get("sample", {})

    korisnici = ucitaj_korisnike()
    if ime not in korisnici:
        return jsonify({"ok": False, "poruka": "Korisnik nije pronađen. Prvo napravite registraciju."}), 404

    try:
        profil = dohvati_profil(korisnici[ime])
        trenutni = izdvoji_znacajke(uzorak)
    except (ValueError, KeyError) as greska:
        return jsonify({"ok": False, "poruka": str(greska)}), 400

    if profil.shape[0] != trenutni.shape[0]:
        return jsonify({"ok": False, "poruka": "Spremljeni profil nema isti broj značajki kao novi uzorak."}), 400

    udaljenost = float(np.linalg.norm(profil - trenutni))
    odobren = udaljenost < PRAG_UDALJENOSTI

    return jsonify({
        "ok": True,
        "odobren": odobren,
        "poruka": "PRISTUP ODOBREN" if odobren else "PRISTUP ODBIJEN",
        "udaljenost": round(udaljenost, 4),
        "prag": PRAG_UDALJENOSTI
    })


if __name__ == "__main__":
    inicijaliziraj_model()
    app.run(debug=True, host="127.0.0.1", port=5000)
