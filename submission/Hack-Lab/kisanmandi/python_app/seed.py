
from datetime import date, timedelta
import random

from database import get_conn, init_db

random.seed(42)
init_db()

crops = [
    ("Wheat", "Grains"),
    ("Rice", "Grains"),
    ("Cotton", "Cash Crops"),
    ("Sugarcane", "Cash Crops"),
    ("Tomato", "Vegetables"),
    ("Onion", "Vegetables"),
    ("Mango", "Fruits"),
    ("Banana", "Fruits"),
]

markets = [
    ("Hyderabad Mandi", "Hyderabad"),
    ("Sukkur Mandi", "Sukkur"),
    ("Mirpurkhas Mandi", "Mirpurkhas"),
]

users = [
    ("Ali Khan", "03000000001", "Hyderabad", "Farmer"),
    ("Sara Ahmed", "03000000002", "Sukkur", "Buyer"),
    ("Imran Shah", "03000000003", "Mirpurkhas", "Farmer"),
    ("Ayesha Memon", "03000000004", "Hyderabad", "Buyer"),
    ("Bilal Chandio", "03000000005", "Sukkur", "Farmer"),
    ("Hina Solangi", "03000000006", "Mirpurkhas", "Farmer"),
]

base_prices = {
    "Wheat": 3000, "Rice": 4200, "Cotton": 7500,
    "Sugarcane": 450, "Tomato": 180, "Onion": 120,
    "Mango": 250, "Banana": 160,
}

with get_conn() as conn:
    # Seed only once, so restarting does not duplicate data.
    if conn.execute("SELECT COUNT(*) FROM crops").fetchone()[0] > 0:
        print("Seed data already exists.")
    else:
        conn.executemany(
            "INSERT INTO crops(name, category) VALUES (?, ?)", crops
        )
        conn.executemany(
            "INSERT INTO markets(name, district) VALUES (?, ?)", markets
        )
        conn.executemany(
            """INSERT INTO users(name, phone, district, role)
               VALUES (?, ?, ?, ?)""", users
        )

        crop_ids = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM crops")
        }
        market_ids = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM markets")
        }

        price_rows = []
        today = date.today()

        for crop, base in base_prices.items():
            for market_index, market in enumerate(markets):
                market_name = market[0]
                for days_ago in range(13, -1, -1):
                    day = today - timedelta(days=days_ago)
                    price = round(
                        base
                        * (1 + market_index * 0.035)
                        * random.uniform(0.96, 1.04),
                        2,
                    )
                    price_rows.append((
                        crop_ids[crop],
                        market_ids[market_name],
                        day.isoformat(),
                        price,
                    ))

        conn.executemany(
            """INSERT INTO prices(crop_id, market_id, date, price)
               VALUES (?, ?, ?, ?)""", price_rows
        )

        listing_rows = []
        for i in range(12):
            crop_id = (i % len(crops)) + 1
            user_id = (i % len(users)) + 1
            crop_name = crops[i % len(crops)][0]
            listing_rows.append((
                user_id, crop_id, 100 + i * 10,
                base_prices[crop_name] * 1.02,
                users[i % len(users)][2],
                ["A", "B", "C"][i % 3],
                today.isoformat(), "Active",
            ))

        conn.executemany(
            """INSERT INTO listings
               (user_id, crop_id, quantity, asking_price, district,
                grade, available_from, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            listing_rows,
        )

        alert_rows = [
            (1, 1, 1, "Above", 3100, 1, 0),
            (3, 2, 2, "Below", 4300, 1, 0),
            (5, 3, 3, "Above", 7800, 1, 0),
            (6, 5, 1, "Below", 190, 1, 0),
            (1, 7, 3, "Above", 260, 1, 0),
        ]

        conn.executemany(
            """INSERT INTO alerts
               (user_id, crop_id, market_id, condition, target_price,
                active_status, triggered)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            alert_rows,
        )

        print("Seed data created successfully!")

    counts = {}
    for table in ("users", "crops", "markets", "prices", "listings", "alerts"):
        counts[table] = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

    print(counts)
