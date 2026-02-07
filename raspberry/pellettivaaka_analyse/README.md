# Pellet measurements analysis

Fetch pellet scale rows by time range from MySQL and print the raw rows.

## Install dependencies (Windows)
```powershell
py -3 -m pip install --user -r raspberry\pellettivaaka_analyse\requirements.txt
```

## Run
```powershell
$env:PELLET_DB_PASSWORD = "YOURPASS"
py -3 raspberry\pellettivaaka_analyse\analyse.py --start "2026-02-01 00:00:00" --end "2026-02-02 00:00:00" --csv out.csv
```

### Bash-skripti ilman parametreja
Muokkaa asetukset ja aja:
```bash
cd raspberry/pellettivaaka_analyse
chmod +x run_analyse.sh
./run_analyse.sh
```

### Kulutuslaskenta
Lisää `--consumption` laskeaksesi kulutuksen (kynnys `--threshold`, oletus 0.1):
```powershell
py -3 raspberry\pellettivaaka_analyse\analyse.py --start "2026-02-01" --end "2026-02-02" --consumption --threshold 0.1
```

## Kuvaaja (weight vs. time)
```powershell
py -3 raspberry\pellettivaaka_analyse\analyse.py --start "2026-02-01" --end "2026-02-02" --plot weight.png
# tai näytä ruudulla
py -3 raspberry\pellettivaaka_analyse\analyse.py --start "2026-02-01" --end "2026-02-02" --show-plot
```

## Notes
- Defaults: host `192.168.100.50`, database `pellet_measurements`, user `admin`.
- Reads `time` and `weight` from table `pellet_measurements` and prints them.
- Optional `--csv` writes the same data to a file.
- Pass `--password` or set env `PELLET_DB_PASSWORD`.
