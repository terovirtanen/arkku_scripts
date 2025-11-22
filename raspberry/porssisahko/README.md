# Pörssisähkö Hintamonitori

Tämä projekti hakee pörssisähkön hintatiedot Porssisähkö.net API:sta ja tallentaa ne MySQL-tietokantaan.

## Pikaohje asennukseen

```bash
# 1. Luo virtuaaliympäristö
python3 -m venv venv
source venv/bin/activate

# 2. Asenna riippuvuudet
pip install -r requirements.txt

# 3. Kopioi ja muokkaa konfiguraatio
cp .env.example .env
nano .env  # täytä DB_* muuttujat

# 4. Testaa
./test_run.sh

# 5. Asenna cron
./setup_cron.sh
```

## Asennus

### 1. Luo virtuaaliympäristö (venv)
```bash
# Luo virtuaaliympäristö
python3 -m venv venv

# Aktivoi virtuaaliympäristö
source venv/bin/activate

# Asenna riippuvuudet
pip install -r requirements.txt
```

### Virtuaaliympäristön käyttö
```bash
# Aktivoi aina ennen käyttöä
source venv/bin/activate

# Deaktivoi kun lopetat
deactivate
```

### 2. Konfiguraatio
Kopioi `.env.example` tiedostoksi `.env` ja muokkaa tietokantayhteyden tiedot:

```bash
cp .env.example .env
nano .env
```

Täytä seuraavat kentät:
```
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

### 3. Tietokanta
Skripti luo automaattisesti `porssisahkonet`-tietokannan ja `prices`-taulun ensimmäisellä ajolla.

## Käyttö

### Manuaalinen ajo
```bash
# Aktivoi venv ensin
source venv/bin/activate

# Aja skripti
python3 porssisahko_read.py
```

### Testaus
```bash
# Aktivoi venv ensin
source venv/bin/activate

# Aja testi
./test_run.sh
```

### Cron-asetukset

#### Asenna automaattinen ajo (klo 3:00 ja 15:00)
```bash
./setup_cron.sh
```

#### Poista automaattinen ajo
```bash
./remove_cron.sh
```

## Tietokantarakenne

```sql
CREATE TABLE prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL UNIQUE,
    price DECIMAL(10, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp)
);
```

## Cron-ajastus

Skripti ajetaan automaattisesti:
- **03:00** - Aamuyöllä (uudet hinnat julkaistaan yleensä n. 14:00)
- **15:00** - Iltapäivällä (varmistus ja mahdolliset korjaukset)

## Lokit

Cron-ajojen lokit tallennetaan:
- `logs/porssisahko_cron.log` - Automaattisten ajojen lokit
- `logs/porssisahko_test.log` - Testiajojen lokit

### Lokien seuranta
```bash
# Seuraa automaattisten ajojen lokia
tail -f logs/porssisahko_cron.log

# Katso viimeisimmät tapahtumat
tail -20 logs/porssisahko_cron.log
```

## Vianmääritys

### Tarkista cron-työt
```bash
crontab -l | grep porssisahko
```

### Testaa yhteys tietokantaan
```bash
mysql -h localhost -u your_username -p porssisahkonet
```

### Tarkista Python-riippuvuudet
```bash
pip list | grep -E "(requests|pytz|mysql|dotenv)"
```

### Tarkista API-yhteys
```bash
curl -s https://api.porssisahko.net/v2/latest-prices.json | head -100
```

## Tiedostot

- `porssisahko_read.py` - Pääskripti
- `setup_cron.sh` - Asenna cron-työt
- `remove_cron.sh` - Poista cron-työt  
- `test_run.sh` - Testaa skriptin toiminta
- `requirements.txt` - Python-riippuvuudet
- `.env.example` - Esimerkkikonfiguraatio
- `README.md` - Tämä ohjetiedosto