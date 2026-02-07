# -*- coding: utf-8 -*-
"""
Pellet scale analysis tool.

Fetch rows by time range from MySQL and process measurements.

DB connection:
- host: 192.168.100.50
- database: pellet_measurements
- user: admin
- password: from CLI arg --password or env var PELLET_DB_PASSWORD

Usage examples (Windows PowerShell):
    py -3 raspberry\pellettivaaka_analyse\analyse.py --start "2026-02-01 00:00:00" --end "2026-02-02 00:00:00" --password "YOURPASS"
    $env:PELLET_DB_PASSWORD = "YOURPASS"; py -3 raspberry\pellettivaaka_analyse\analyse.py --start "2026-02-01" --end "2026-02-02"

Outputs:
- Prints fetched rows count and a summary
- Prints min/max/avg weights
- Prints first/last weights and delta
- Prints simple consumption deltas between consecutive points
- Optional CSV output via --csv path
"""
import os
import sys
import argparse
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

try:
    import mysql.connector
except Exception as e:
    print("Missing dependency: mysql-connector-python. Install via:\n  py -3 -m pip install --user mysql-connector-python")
    raise

ROW = Tuple[datetime, float]


def parse_dt(s: str) -> datetime:
    # Accept date-only (YYYY-MM-DD) or full timestamp
    s = s.strip()
    fmts = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid datetime: {s}")


def fetch_rows(start: datetime, end: datetime, password: str, host: str = "192.168.100.50", db: str = "pellet_measurements", user: str = "admin") -> List[ROW]:
    conn = mysql.connector.connect(host=host, database=db, user=user, password=password)
    try:
        cur = conn.cursor()
        # Table name assumed 'pellet_measurements' with columns time (DATETIME) and weight (FLOAT)
        sql = (
            "SELECT time, weight FROM pellet_measurements "
            "WHERE time >= %s AND time <= %s ORDER BY time ASC"
        )
        cur.execute(sql, (start, end))
        rows: List[ROW] = []
        for t, w in cur.fetchall():
            # Connector returns datetime and Decimal/float depending on config
            wt = float(w)
            rows.append((t, wt))
        return rows
    finally:
        conn.close()


# No summary processing: only fetch and output rows (time, weight)

def compute_consumption(rows: List[ROW], threshold: float = 0.1) -> Dict[str, Any]:
    """
    Käy rivit läpi aika-järjestyksessä ja laskee kulutuksen.
    - Jos seuraava weight kasvaa >= threshold -> täyttö (refill)
    - Jos muutos on välillä (-threshold, +threshold) -> anturin kohinaa, skip
    - Jos seuraava weight alenee <= -threshold -> kulutus, lisätään kulutukseen (positiivisena)
    Palauttaa: total_consumption, events (lista), counts
    """
    total_consumption = 0.0
    events: List[Dict[str, Any]] = []
    noise_skipped = 0
    if not rows:
        return {
            "total_consumption": 0.0,
            "events": events,
            "refill_count": 0,
            "consumption_count": 0,
            "noise_skipped": 0,
        }
    for i in range(len(rows) - 1):
        t0, w0 = rows[i]
        t1, w1 = rows[i + 1]
        diff = w1 - w0
        if diff >= threshold:
            events.append({
                "type": "refill",
                "from_time": t0,
                "to_time": t1,
                "delta": diff,
            })
        elif diff <= -threshold:
            cons = -diff
            total_consumption += cons
            events.append({
                "type": "consumption",
                "from_time": t0,
                "to_time": t1,
                "delta": cons,
            })
        else:
            noise_skipped += 1
            events.append({
                "type": "noise",
                "from_time": t0,
                "to_time": t1,
                "delta": diff,
            })
    refill_count = sum(1 for e in events if e["type"] == "refill")
    consumption_count = sum(1 for e in events if e["type"] == "consumption")
    return {
        "total_consumption": total_consumption,
        "events": events,
        "refill_count": refill_count,
        "consumption_count": consumption_count,
        "noise_skipped": noise_skipped,
    }


def plot_weight(rows: List[ROW], outfile: Optional[str] = None, title: Optional[str] = None, ylabel: str = "Weight (kg)") -> None:
    """Piirtää kuvaajan (aika vs. weight). Tallentaa tiedostoon jos outfile annettu."""
    if not rows:
        print("No rows to plot.")
        return
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except Exception:
        print("matplotlib puuttuu. Asenna: py -3 -m pip install --user matplotlib")
        return

    times, weights = zip(*rows)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, weights, marker='.', linewidth=1.0)
    ax.set_xlabel('Time')
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(True, alpha=0.3)

    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    if outfile:
        fig.savefig(outfile, dpi=150, bbox_inches='tight')
        print(f"Plot written: {outfile}")
        plt.close(fig)
    else:
        plt.show()


def to_csv(rows: List[ROW]) -> str:
    lines = ["time,weight"]
    for t, w in rows:
        # ISO format without timezone
        lines.append(f"{t.strftime('%Y-%m-%d %H:%M:%S')},{w}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Pellet measurements fetch and process")
    ap.add_argument("--start", required=True, help="Start time (YYYY-MM-DD[ HH:MM[:SS]])")
    ap.add_argument("--end", required=True, help="End time (YYYY-MM-DD[ HH:MM[:SS]])")
    ap.add_argument("--password", help="DB password (or set env PELLET_DB_PASSWORD)")
    ap.add_argument("--host", default="192.168.100.50")
    ap.add_argument("--db", default="pellet_measurements")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--csv", help="Optional CSV output path")
    ap.add_argument("--consumption", action="store_true", help="Laske ja tulosta kulutus (kynnys oletus 0.1)")
    ap.add_argument("--threshold", type=float, default=0.1, help="Kynnysarvo kg (oletus 0.1)")
    ap.add_argument("--plot", help="Tallenna kuvaaja polkuun (esim. out.png)")
    ap.add_argument("--show-plot", action="store_true", help="Näytä kuvaaja näytöllä")
    args = ap.parse_args(argv)

    pw = args.password or os.environ.get("PELLET_DB_PASSWORD")
    if not pw:
        print("Error: provide --password or set env PELLET_DB_PASSWORD.")
        return 2

    start = parse_dt(args.start)
    end = parse_dt(args.end)
    if end < start:
        print("Error: end must be >= start")
        return 2

    rows = fetch_rows(start, end, password=pw, host=args.host, db=args.db, user=args.user)
    print(f"Fetched {len(rows)} rows between {start} and {end}.")

    if args.csv:
        csv_data = to_csv(rows)
        with open(args.csv, "w", encoding="utf-8") as f:
            f.write(csv_data)
        print(f"CSV written: {args.csv}")
    # Print rows to stdout (time,weight)
    if rows:
        print("Rows:")
        for t, w in rows:
            print(f"  {t.strftime('%Y-%m-%d %H:%M:%S')}, {w}")

    if args.consumption:
        cons = compute_consumption(rows, threshold=args.threshold)
        print("Consumption:")
        print(f"  total: {cons['total_consumption']:.3f}")
        print(f"  refills: {cons['refill_count']}  segments: {cons['consumption_count']}  noise_skipped: {cons['noise_skipped']}")
        # Tulosta vain kulutus-tapahtumat lyhyesti
        for e in cons["events"]:
            if e["type"] == "consumption":
                ft = e["from_time"].strftime('%Y-%m-%d %H:%M:%S')
                tt = e["to_time"].strftime('%Y-%m-%d %H:%M:%S')
                print(f"    {ft} -> {tt}: -{e['delta']:.3f}")

    if args.plot or args.show_plot:
        title = f"Weight over time ({start} .. {end})"
        plot_weight(rows, outfile=args.plot, title=title)

    return 0


if __name__ == "__main__":
    sys.exit(main())
