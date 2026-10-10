"""
ParkTrack 360 — server/db.py
SQLite database layer for events, vehicle visits, parking sessions, and persistent car state.
"""

import sqlite3
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path("parktrack.db")

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DB_PATH):
    """Initializes tables and seeds initial car states if not present."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            type TEXT NOT NULL,
            car INTEGER,
            slot TEXT,
            detail TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car INTEGER NOT NULL,
            entry_ts TEXT NOT NULL,
            exit_ts TEXT,
            inside_s REAL,
            parked_s REAL,
            fare REAL DEFAULT 0.0,
            payment_status TEXT DEFAULT 'PENDING'
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS parkings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER,
            car INTEGER,
            slot TEXT NOT NULL,
            start_ts TEXT NOT NULL,
            end_ts TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS car_state (
            car INTEGER PRIMARY KEY,
            state TEXT NOT NULL,
            slot TEXT,
            entered_ts TEXT,
            visit_id INTEGER
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);")

        # Seed car_state for cars 1 to 8 if table is empty
        cursor.execute("SELECT COUNT(*) FROM car_state")
        count = cursor.fetchone()[0]
        if count == 0:
            for car_id in range(1, 9):
                cursor.execute("""
                    INSERT INTO car_state (car, state, slot, entered_ts, visit_id)
                    VALUES (?, 'OUTSIDE', NULL, NULL, NULL)
                """, (car_id,))
        
        # Seed default stats epoch
        cursor.execute("SELECT value FROM meta WHERE key = 'stats_epoch_ts'")
        if not cursor.fetchone():
            now_iso = datetime.datetime.now().astimezone().isoformat()
            cursor.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('stats_epoch_ts', ?)", (now_iso,))
            cursor.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', '1.1')")

        conn.commit()

def log_event(event_type: str, car: Optional[int] = None, slot: Optional[str] = None, detail: Optional[str] = None, db_path: Path = DB_PATH):
    now_iso = datetime.datetime.now().astimezone().isoformat()
    with get_connection(db_path) as conn:
        conn.cursor().execute("""
            INSERT INTO events (ts, type, car, slot, detail)
            VALUES (?, ?, ?, ?, ?)
        """, (now_iso, event_type, car, slot, detail))
        conn.commit()

def get_recent_events(limit: int = 50, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ts, type, car, slot, detail FROM events ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

def load_car_states(db_path: Path = DB_PATH) -> Dict[int, Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT car, state, slot, entered_ts, visit_id FROM car_state")
        return {row["car"]: dict(row) for row in cursor.fetchall()}

def save_car_state(car: int, state: str, slot: Optional[str] = None, entered_ts: Optional[str] = None, visit_id: Optional[int] = None, db_path: Path = DB_PATH):
    with get_connection(db_path) as conn:
        conn.cursor().execute("""
            UPDATE car_state
            SET state = ?, slot = ?, entered_ts = ?, visit_id = ?
            WHERE car = ?
        """, (state, slot, entered_ts, visit_id, car))
        conn.commit()

def start_visit(car: int, db_path: Path = DB_PATH) -> int:
    now_iso = datetime.datetime.now().astimezone().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO visits (car, entry_ts, exit_ts, inside_s, parked_s, fare, payment_status)
            VALUES (?, ?, NULL, NULL, 0.0, 0.0, 'PENDING')
        """, (car, now_iso))
        conn.commit()
        return cursor.lastrowid

def close_visit(visit_id: int, inside_s: float, parked_s: float, fare: float = 0.0, db_path: Path = DB_PATH):
    now_iso = datetime.datetime.now().astimezone().isoformat()
    with get_connection(db_path) as conn:
        conn.cursor().execute("""
            UPDATE visits
            SET exit_ts = ?, inside_s = ?, parked_s = ?, fare = ?, payment_status = 'COMPLETED'
            WHERE id = ?
        """, (now_iso, inside_s, parked_s, fare, visit_id))
        conn.commit()

def start_parking(visit_id: Optional[int], car: int, slot: str, db_path: Path = DB_PATH) -> int:
    now_iso = datetime.datetime.now().astimezone().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO parkings (visit_id, car, slot, start_ts, end_ts)
            VALUES (?, ?, ?, ?, NULL)
        """, (visit_id, car, slot, now_iso))
        conn.commit()
        return cursor.lastrowid

def end_parking(parking_id: int, db_path: Path = DB_PATH):
    now_iso = datetime.datetime.now().astimezone().isoformat()
    with get_connection(db_path) as conn:
        conn.cursor().execute("""
            UPDATE parkings
            SET end_ts = ?
            WHERE id = ?
        """, (now_iso, parking_id))
        conn.commit()

def get_stats(epoch_ts: Optional[str] = None, db_path: Path = DB_PATH) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if not epoch_ts:
            cursor.execute("SELECT value FROM meta WHERE key = 'stats_epoch_ts'")
            row = cursor.fetchone()
            epoch_ts = row[0] if row else datetime.datetime.now().astimezone().isoformat()

        # Entries since epoch
        cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'entry' AND ts >= ?", (epoch_ts,))
        entries_today = cursor.fetchone()[0]

        # Exits since epoch
        cursor.execute("SELECT COUNT(*) FROM events WHERE type = 'exit' AND ts >= ?", (epoch_ts,))
        exits_today = cursor.fetchone()[0]

        # Per car summary
        per_car = []
        for car_id in range(1, 9):
            cursor.execute("""
                SELECT COUNT(*), AVG(inside_s), AVG(parked_s)
                FROM visits
                WHERE car = ? AND entry_ts >= ? AND exit_ts IS NOT NULL
            """, (car_id, epoch_ts))
            cnt, avg_in, avg_pk = cursor.fetchone()
            
            cursor.execute("""
                SELECT inside_s FROM visits
                WHERE car = ? AND entry_ts >= ? AND exit_ts IS NOT NULL
                ORDER BY id DESC LIMIT 1
            """, (car_id, epoch_ts))
            last_in_row = cursor.fetchone()
            last_in = last_in_row[0] if last_in_row else None

            per_car.append({
                "car": car_id,
                "visits_today": cnt or 0,
                "avg_inside_s": round(avg_in, 1) if avg_in is not None else 0.0,
                "avg_parked_s": round(avg_pk, 1) if avg_pk is not None else 0.0,
                "last_inside_s": round(last_in, 1) if last_in is not None else None
            })

        return {
            "entries_today": entries_today,
            "exits_today": exits_today,
            "epoch_ts": epoch_ts,
            "per_car": per_car
        }

def reset_stats(db_path: Path = DB_PATH) -> str:
    now_iso = datetime.datetime.now().astimezone().isoformat()
    with get_connection(db_path) as conn:
        conn.cursor().execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('stats_epoch_ts', ?)", (now_iso,))
        conn.commit()
    return now_iso
