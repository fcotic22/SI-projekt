import pandas as pd
import numpy as np
import time
import os
import json
import joblib
import sys
from pynput import keyboard
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.getcwd()
DATASET_PATH = os.path.join(BASE_DIR, 'datasetStaticka', 'DSL-StrongPasswordData.csv')
MODEL_FILE = os.path.join(BASE_DIR, 'keystroke_model.joblib')
USERS_FILE = os.path.join(BASE_DIR, 'korisnici_profili.json')
KLJUČNA_RIJEČ = ".tie5Roanl"

BROJ_PONAVLJANJA = 3

PRAG_UDALJENOSTI = 0.8


class KeystrokeSustav:
    def __init__(self):
        self.model = None
        self.le = LabelEncoder()
        self.registrirani_korisnici = self.ucitaj_ili_kreiraj_korisnike()
        self.keystroke_data = []
        self.pressed_times = {}
        self.trenutni_string = ""
        self.inicijaliziraj_model()

    def ucitaj_ili_kreiraj_korisnike(self):
        if not os.path.exists(USERS_FILE):
            print(f">>> Datoteka {USERS_FILE} ne postoji. Kreiram novi prazni rječnik...")
            with open(USERS_FILE, 'w') as f:
                json.dump({}, f)
            return {}
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(">>> Greška pri čitanju baze. Kreiram novi rječnik...")
            return {}

    def spremi_korisnika(self, ime, profil_vektor):
        if isinstance(profil_vektor, np.ndarray):
            profil_1d = profil_vektor.flatten().tolist()
        else:
            profil_1d = list(np.array(profil_vektor).flatten())

        self.registrirani_korisnici[ime] = profil_1d
        with open(USERS_FILE, 'w') as f:
            json.dump(self.registrirani_korisnici, f, indent=2)
        print(f"\n Korisnik '{ime}' je uspješno registriran u bazi.")

    def inicijaliziraj_model(self):
        if os.path.exists(MODEL_FILE):
            self.model = joblib.load(MODEL_FILE)
            if os.path.exists(DATASET_PATH):
                df = pd.read_csv(DATASET_PATH)
                self.le.fit(df['subject'])
            print(">>> Model učitan.")
        else:
            print(">>> Model nije pronađen. Pokrećem treniranje...")
            self.treniraj_i_spremi()

    def treniraj_i_spremi(self):
        if not os.path.exists(DATASET_PATH):
            return
        df = pd.read_csv(DATASET_PATH)
        X = df.iloc[:, 3:]
        y = self.le.fit_transform(df['subject'])
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        joblib.dump(self.model, MODEL_FILE)
        print(">>> Model uspješno istreniran i spremljen.")

    def ocisti_buffer(self):
        time.sleep(0.05)
        try:
            if os.name == 'nt':
                import msvcrt
                while msvcrt.kbhit():
                    msvcrt.getch()
            else:
                import termios
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except Exception:
            pass

    def on_press(self, key):
        try:
            k = key.char
        except AttributeError:
            if key == keyboard.Key.backspace:
                k = "backspace"
            elif key == keyboard.Key.enter:
                k = "enter"
            else:
                k = str(key)

        if k not in self.pressed_times:
            self.pressed_times[k] = time.time()

    def on_release(self, key):
        release_time = time.time()

        # ENTER
        if key == keyboard.Key.enter:
            self.pressed_times.pop("enter", None)
            if len(self.trenutni_string) == 0:
                return True
            print("")
            return False

        if key == keyboard.Key.backspace:
            self.pressed_times.pop("backspace", None)
            if self.trenutni_string:                
                zadnji_znak = self.trenutni_string[-1]
                self.trenutni_string = self.trenutni_string[:-1]                
                print('\b \b', end='', flush=True)
                if self.keystroke_data:
                    self.keystroke_data.pop()
                self.pressed_times.pop(zadnji_znak, None)
            return

        try:
            k = key.char
        except AttributeError:
            self.pressed_times.pop(str(key), None)
            return

        if not k:
            return

        print(k, end='', flush=True)
        self.trenutni_string += k

        if k in self.pressed_times:
            press_time = self.pressed_times.pop(k)
            self.keystroke_data.append({
                'key': k,
                'press': press_time,
                'release': release_time
            })

    #  SNIMANJE UNOSA                                                      
    def snimi_unos(self, poruka):
        print(f"\n{poruka} '{KLJUČNA_RIJEČ}':", end=' ', flush=True)
        self.ocisti_buffer()
        self.keystroke_data = []
        self.pressed_times = {}
        self.trenutni_string = ""

        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            listener.join()

        self.ocisti_buffer()

        if self.trenutni_string != KLJUČNA_RIJEČ:
            print(f" Unijeli ste '{self.trenutni_string}'. "
                  "Ključna riječ nije ispravna. Pokušajte ponovno.")
            return None

        return self.izracunaj_znacajke()

    #  EKSTRAKCIJA ZNAČAJKI                                                
    def izracunaj_znacajke(self):
        n = len(KLJUČNA_RIJEČ)
        if len(self.keystroke_data) != n:
            print(f" Snimljeno {len(self.keystroke_data)} od {n} znakova. "
                  "Biometrijski uzorak nije valjan.")
            return None

        vremena = []
        for i in range(n):
            # Dwell Time
            dt = self.keystroke_data[i]['release'] - self.keystroke_data[i]['press']
            vremena.append(dt)
            # Flight Time
            if i < n - 1:
                ft = self.keystroke_data[i + 1]['press'] - self.keystroke_data[i]['release']
                vremena.append(ft)
        return np.array(vremena).reshape(1, -1)

    #  REGISTRACIJA                                                        
    def registriraj_korisnika(self, ime):
        if ime in self.registrirani_korisnici:
            print(f"\n Korisnik '{ime}' već postoji u bazi.")
            print("  Ako želite resetirati profil, kontaktirajte administratora.")
            return

        print(f"\n=== REGISTRACIJA: {ime} ===")
        print(f"Trebate upisati ključnu riječ {BROJ_PONAVLJANJA} puta za kalibraciju.")

        uzorci = []
        pokusaj = 1
        while len(uzorci) < BROJ_PONAVLJANJA:
            print(f"\n[{len(uzorci) + 1}/{BROJ_PONAVLJANJA}] Pokušaj {pokusaj}:")
            vektor = self.snimi_unos("Utipkajte")
            pokusaj += 1
            if vektor is not None:
                uzorci.append(vektor.flatten())
            else:
                print("  Uzorak odbačen. Pokušajte ponovo.")

        profil = np.mean(uzorci, axis=0)
        self.spremi_korisnika(ime, profil)

    #  PRIJAVA                                                             
    def prijavi_korisnika(self, ime):
        if ime not in self.registrirani_korisnici:
            print(f"Korisnik '{ime}' nije pronađen u bazi. "
                  "Odaberite opciju 2 za registraciju.")
            return

        pohranjeno = np.array(self.registrirani_korisnici[ime]).flatten()

        MAX_POKUSAJA = 3
        for pokusaj in range(1, MAX_POKUSAJA + 1):
            print(f"\n[Pokušaj {pokusaj}/{MAX_POKUSAJA}]")
            vektor = self.snimi_unos("Utipkajte")

            if vektor is None:
                print("  Uzorak neispravan.")
                continue

            trenutni = vektor.flatten()
            distanca = np.linalg.norm(pohranjeno - trenutni)

            print("\n--- REZULTAT PROVJERE ---")
            print(f"  Euklidska udaljenost: {distanca:.4f}  (prag: {PRAG_UDALJENOSTI})")

            if distanca < PRAG_UDALJENOSTI:
                print(f" PRISTUP ODOBREN! Dobrodošli, {ime}!")
                return
            else:
                print(f"PRISTUP ODBIJEN. Ritam tipkanja ne odgovara.")
                if pokusaj < MAX_POKUSAJA:
                    print("  Pokušajte ponovo.")

        print(f"\n ZABRANJEN ULAZ")

#  GLAVNI PROGRAM                                                      
if __name__ == "__main__":
    sustav = KeystrokeSustav()

    while True:
        sustav.ocisti_buffer()
        ime = input("\nUnesite vaše ime (ili 'exit' za kraj): ").strip()
        if not ime:
            continue
        if ime.lower() == 'exit':
            break

        print(f"\n--- KORISNIK: {ime} ---")
        print("1. Prijava")
        print("2. Registracija")
        izbor = input("Odaberite opciju (1/2): ").strip()

        if izbor == '1':
            sustav.prijavi_korisnika(ime)

        elif izbor == '2':
            sustav.registriraj_korisnika(ime)

        else:
            print("Nepoznata opcija. Odaberi 1 ili 2.")