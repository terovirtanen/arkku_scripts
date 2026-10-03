# php_car_charger

Lisää `car_charger`-tauluun (kanta `porssisahkonet`) latausjakson, joka alkaa nykyhetkestä.

## Endpoint

`GET /car_charger/start_now`

| Parametri | Arvot | Oletus | Kuvaus |
|---|---|---|---|
| `hours` | 1, 2, 3 | 1 | Latausjakson pituus tunteina |
| `power_charging` | true, false | false | false -> `solar` (10 A), true -> `solar_max` (16 A) |

## Esimerkit

Oletus (1 h, 10 A):

```
curl -L "http://<palvelin>/car_charger/start_now"
```

2 h teholatauksella (16 A):

```
curl -L "http://<palvelin>/car_charger/start_now?hours=2&power_charging=true"
```

Vastaus:

```json
{
  "success": true,
  "message": "Charging period added",
  "data": {
    "id": 1,
    "start_time": "2026-10-03 12:00:00",
    "end_time": "2026-10-03 14:00:00",
    "hours": 2,
    "period_type": "solar_max"
  }
}
```

## Asennus

1. Kopioi `.env.example` nimelle `.env` ja täytä tunnukset.
2. Aja `./apache_setup.sh`.
