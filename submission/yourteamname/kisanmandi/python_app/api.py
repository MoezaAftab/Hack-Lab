
from typing import Any
import sqlite3

from fastapi import FastAPI, HTTPException
from database import DB_PATH, init_db

app = FastAPI(title="KisanMandi API")

TABLES = {
    "users", "crops", "markets", "prices", "listings", "alerts"
}

init_db()


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@app.get("/")
def home():
    return {"message": "KisanMandi API is running"}


@app.get("/{table}")
def get_items(table: str):
    if table not in TABLES:
        raise HTTPException(404, "Collection not found")

    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        return [dict(row) for row in rows]


@app.post("/{table}", status_code=201)
def create_item(table: str, item: dict[str, Any]):
    if table not in TABLES:
        raise HTTPException(404, "Collection not found")

    with connect() as conn:
        columns = {
            row["name"] for row in
            conn.execute(f"PRAGMA table_info({table})")
        }
        data = {k: v for k, v in item.items() if k in columns and k != "id"}

        if not data:
            raise HTTPException(400, "No valid fields provided")

        keys = list(data)
        sql = (
            f"INSERT INTO {table} "
            f"({', '.join(keys)}) VALUES "
            f"({', '.join('?' for _ in keys)})"
        )

        try:
            cursor = conn.execute(sql, list(data.values()))
            row = conn.execute(
                f"SELECT * FROM {table} WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return dict(row)
        except sqlite3.IntegrityError as exc:
            raise HTTPException(400, str(exc))


@app.patch("/{table}/{item_id}")
def update_item(table: str, item_id: int, item: dict[str, Any]):
    if table not in TABLES:
        raise HTTPException(404, "Collection not found")

    with connect() as conn:
        columns = {
            row["name"] for row in
            conn.execute(f"PRAGMA table_info({table})")
        }
        data = {k: v for k, v in item.items() if k in columns and k != "id"}

        if not data:
            raise HTTPException(400, "No valid fields provided")

        keys = list(data)
        try:
            cursor = conn.execute(
                f"UPDATE {table} SET "
                + ", ".join(f"{key} = ?" for key in keys)
                + " WHERE id = ?",
                list(data.values()) + [item_id],
            )
            if cursor.rowcount == 0:
                raise HTTPException(404, "Item not found")
            row = conn.execute(
                f"SELECT * FROM {table} WHERE id = ?", (item_id,)
            ).fetchone()
            return dict(row)
        except sqlite3.IntegrityError as exc:
            raise HTTPException(400, str(exc))


@app.delete("/{table}/{item_id}")
def delete_item(table: str, item_id: int):
    if table not in TABLES:
        raise HTTPException(404, "Collection not found")

    with connect() as conn:
        cursor = conn.execute(
            f"DELETE FROM {table} WHERE id = ?", (item_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(404, "Item not found")
        return {"deleted": True, "id": item_id}
