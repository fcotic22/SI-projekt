==================================================
STRUKTURA PROJEKTA
==================================================

app.py
- Pokreće Flask web server.
- Povezuje web stranicu s Python logikom.
- Prima zahtjeve za registraciju i prijavu korisnika.
- Poziva funkcije iz drugih Python datoteka.

Ključne stvari:
- ruta "/" prikazuje početnu web stranicu
- ruta "/api/register" služi za registraciju korisnika
- ruta "/api/login" služi za prijavu korisnika
- ruta "/api/users" vraća popis spremljenih korisnika


config.py
- Datoteka s glavnim postavkama sustava.
- Ovdje se mijenjaju osnovne vrijednosti bez diranja ostatka koda.

Ključne stvari:
- REGISTRATION_SAMPLES = broj uzoraka za registraciju
- MIN_CHARS = minimalan broj znakova u jednom uzorku
- DISTANCE_THRESHOLD = prag za odluku o prijavi
- USERS_FILE = putanja do datoteke u kojoj se spremaju korisnici


storage.py
- Zadužen za spremanje i učitavanje korisnika.
- Radi s datotekom data/users.json.
- Ako users.json ne postoji, automatski ga napravi.

Ključne stvari:
- load_users() učitava spremljene korisnike
- save_users() sprema korisnike
- ensure_storage() provjerava postoji li data folder i users.json


features.py
- Iz podataka o tipkanju računa značajke.
- Ovo je jedna od najvažnijih datoteka.
- Prima sirove podatke o tipkanju i pretvara ih u brojeve.

Sustav računa:
- prosječno trajanje pritiska tipke
- razmak između dvije tipke
- brzinu tipkanja
- učestalost Backspace tipke
- udio razmaka
- udio velikih slova
- udio brojeva
- udio interpunkcije
- udio Enter tipke

Ključne funkcije:
- extract_features() izvlači značajke iz jednog uzorka tipkanja
- clean_events() čisti neispravne događaje tipkanja
- stats() računa prosjek, standardnu devijaciju, medijan, minimum i maksimum


auth_logic.py
- Zadužen za logiku registracije i prijave.
- Koristi značajke iz features.py.
- Iz više uzoraka radi korisnički profil.
- Kod prijave uspoređuje novi uzorak sa spremljenim profilom.

Ključne funkcije:
- create_user_profile() stvara profil korisnika
- check_login() provjerava smije li korisnik ući
- calculate_distance() računa koliko se novi uzorak razlikuje od profila


templates/index.html
- Glavna HTML stranica.
- Prikazuje korisničko sučelje u pregledniku.
- Sadrži polje za korisničko ime, tekstualno polje i gumbe.

Ključne stvari:
- gumb za registraciju
- gumb za prijavu
- textarea za slobodno tipkanje
- prikaz rezultata prijave


static/css/style.css
- Datoteka za izgled web stranice.
- Uređuje boje, gumbe, tekstualno polje i raspored elemenata.
- Nema logiku sustava, samo izgled.


static/js/typing.js
- JavaScript datoteka koja radi u pregledniku.
- Bilježi kada je tipka pritisnuta i kada je puštena.
- Sprema podatke o tipkanju i šalje ih Python aplikaciji.

Ključne stvari:
- keydown bilježi trenutak pritiska tipke
- keyup bilježi trenutak otpuštanja tipke
- šalje podatke na /api/register ili /api/login


data/users.json
- Datoteka u koju se spremaju registrirani korisnici.
- Nakon registracije u nju se sprema profil korisnika.
- Na početku može sadržavati samo prazni objekt:

==================================================
REGISTRACIJA
==================================================

Kod registracije korisnik piše više uzoraka slobodnog teksta.

Nakon toga sustav:
1. uzima sve uzorke
2. iz svakog uzorka računa značajke
3. računa prosječni profil korisnika
4. sprema profil u data/users.json

Profil korisnika predstavlja njegov prosječni način tipkanja.

==================================================
PRIJAVA
==================================================

Kod prijave korisnik piše jedan novi slobodni tekst.

Sustav tada:
1. iz novog teksta računa značajke
2. učitava spremljeni profil korisnika iz users.json
3. uspoređuje novi uzorak sa spremljenim profilom
4. računa distance
5. uspoređuje distance s threshold vrijednosti
6. odlučuje je li pristup odobren ili odbijen

==================================================
OSTALO
==================================================

Distance je broj koji pokazuje koliko se trenutni uzorak tipkanja razlikuje od spremljenog profila korisnika.

Manji distance znači:
- korisnik tipka slično kao kod registracije
- veća je šansa da je to isti korisnik

Veći distance znači:
- korisnik tipka drugačije
- veća je šansa da to nije isti korisnik


Threshold je granica za odluku o prijavi.
Ako je threshold veći, sustav je blaži.
Ako je threshold manji, sustav je stroži.


ZNAČAJKE:
Značajke su brojevi koji opisuju kako korisnik tipka.

hold time
- koliko dugo korisnik drži tipku pritisnutu

press-press time
- vrijeme od pritiska jedne tipke do pritiska sljedeće tipke

release-press time
- vrijeme od otpuštanja jedne tipke do pritiska sljedeće tipke

chars per second
- brzina tipkanja izražena u znakovima po sekundi

backspace rate
- koliko često korisnik koristi Backspace

space rate
- koliko često korisnik koristi razmak

uppercase rate
- koliko često korisnik koristi velika slova

punctuation rate
- koliko često korisnik koristi interpunkciju


==================================================
KADA SE KOJA DATOTEKA KORISTI
==================================================

Kada se pokrene aplikacija:
1. Pokreće se app.py
2. app.py učitava postavke iz config.py
3. app.py pokreće Flask server
4. Flask prikazuje templates/index.html
5. index.html učitava style.css i typing.js


Kada korisnik tipka:
1. typing.js bilježi pritisak i otpuštanje tipki
2. typing.js sprema typedText i events
3. klikom na Save current sample podaci se šalju u app.py


Kada se radi registracija:
1. app.py prima podatke na /api/register
2. app.py poziva create_user_profile() iz auth_logic.py
3. auth_logic.py poziva extract_features() iz features.py
4. features.py računa značajke tipkanja
5. auth_logic.py radi profil korisnika
6. app.py poziva save_users() iz storage.py
7. storage.py sprema profil u data/users.json


Kada se radi prijava:
1. app.py prima podatke na /api/login
2. app.py poziva load_users() iz storage.py
3. storage.py učitava spremljene korisnike iz data/users.json
4. app.py poziva check_login() iz auth_logic.py
5. auth_logic.py poziva extract_features() iz features.py
6. features.py računa značajke novog uzorka
7. auth_logic.py računa distance
8. auth_logic.py uspoređuje distance i threshold
9. app.py vraća rezultat web stranici
10. typing.js prikazuje ACCESS APPROVED ili ACCESS DENIED