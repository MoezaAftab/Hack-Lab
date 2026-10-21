
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("kisanmandi.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            district TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            district TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY,
            crop_id INTEGER NOT NULL,
            market_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(crop_id) REFERENCES crops(id),
            FOREIGN KEY(market_id) REFERENCES markets(id)
        );

        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            crop_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            asking_price REAL NOT NULL,
            district TEXT NOT NULL,
            grade TEXT NOT NULL,
            available_from TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(crop_id) REFERENCES crops(id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            crop_id INTEGER NOT NULL,
            market_id INTEGER NOT NULL,
            condition TEXT NOT NULL,
            target_price REAL NOT NULL,
            active_status INTEGER NOT NULL DEFAULT 1,
            triggered INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(crop_id) REFERENCES crops(id),
            FOREIGN KEY(market_id) REFERENCES markets(id)
        );
        """)
