import sqlite3
from typing import Optional

DB_FILE = "lemonade_stand.db"


def get_connection() -> sqlite3.Connection:
    """Returns a connection configured for dictionary rows and foreign keys."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(starting_cash: float = 100.0) -> None:
    """Creates tables with strict integrity constraints and seeds initial stock."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Treasury: Single-row business cash balance
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS treasury (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                balance REAL NOT NULL CHECK (balance >= 0)
            );
            """
        )

        # Inventory: Stock counts, wholesale costs, retail pricing
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                stock INTEGER NOT NULL CHECK (stock >= 0),
                cost_price REAL NOT NULL CHECK (cost_price >= 0),
                sale_price REAL NOT NULL CHECK (sale_price >= 0)
            );
            """
        )

        # Ledger: Immutable operational audit trail
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                entry_type TEXT CHECK (entry_type IN ('SALE', 'RESTOCK')),
                sku TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY (sku) REFERENCES inventory (sku)
            );
            """
        )

        # Seed initial treasury if not already present
        cursor.execute("SELECT balance FROM treasury WHERE id = 1;")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO treasury (id, balance) VALUES (1, ?);",
                (starting_cash,),
            )

        # Seed baseline catalog
        seed_items = [
            ("LEMON_CUP", "Fresh Lemonade Cup", 20, 0.75, 2.50),
            ("COOKIE", "Chocolate Chip Cookie", 12, 0.50, 1.50),
            ("ICE_WATER", "Cold Ice Water", 25, 0.10, 1.00),
            ("TIP", "Customer Gratuity", 0, 0.00, 0.00),
        ]
        cursor.executemany(
            """
            INSERT OR IGNORE INTO inventory (sku, name, stock, cost_price, sale_price)
            VALUES (?, ?, ?, ?, ?);
            """,
            seed_items,
        )

        conn.commit()
    print("[DB] Initialized database and seeded baseline records.")


if __name__ == "__main__":
    init_db()