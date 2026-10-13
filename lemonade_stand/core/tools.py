import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

_STAND_DIR = Path(__file__).resolve().parent.parent
if str(_STAND_DIR) not in sys.path:
    sys.path.insert(0, str(_STAND_DIR))

try:
    from core.db import get_connection
except (ImportError, ModuleNotFoundError):
    from lemonade_stand.core.db import get_connection




def get_treasury_balance() -> float:
    """Returns the current liquid cash balance of the store."""
    with get_connection() as conn:
        row = conn.execute("SELECT balance FROM treasury WHERE id = 1;").fetchone()
        return round(row["balance"], 2) if row else 0.0


def get_inventory_status() -> List[Dict[str, Any]]:
    """Returns all inventory items, stock counts, wholesale costs, and retail sale prices."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT sku, name, stock, sale_price, cost_price FROM inventory WHERE sku != 'TIP';"
        ).fetchall()
        return [dict(r) for r in rows]


def get_recent_transactions(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns the most recent ledger transactions for auditing and review."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp, entry_type, sku, quantity, unit_price, total_amount
            FROM ledger
            ORDER BY id DESC
            LIMIT ?;
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def execute_sale(sku: str, quantity: int) -> Dict[str, Any]:
    """
    Executes a customer sale: checks stock, decrements inventory,
    credits treasury revenue, and writes an audit ledger record.
    """
    if quantity <= 0:
        return {"success": False, "error": "Quantity must be greater than zero."}

    with get_connection() as conn:
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT stock, sale_price, name FROM inventory WHERE sku = ?;", (sku,))
            item = cursor.fetchone()
            if not item:
                return {"success": False, "error": f"Item '{sku}' does not exist in catalog."}

            current_stock = item["stock"]
            sale_price = item["sale_price"]

            if current_stock < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient stock for '{sku}'. Requested {quantity}, but only {current_stock} in stock.",
                }

            total_revenue = round(sale_price * quantity, 2)

            cursor.execute("UPDATE inventory SET stock = stock - ? WHERE sku = ?;", (quantity, sku))
            cursor.execute("UPDATE treasury SET balance = balance + ? WHERE id = 1;", (total_revenue,))
            cursor.execute(
                """
                INSERT INTO ledger (entry_type, sku, quantity, unit_price, total_amount)
                VALUES ('SALE', ?, ?, ?, ?);
                """,
                (sku, quantity, sale_price, total_revenue),
            )

            conn.commit()
            return {
                "success": True,
                "message": f"Sold {quantity}x {item['name']} for ${total_revenue:.2f}.",
                "revenue": total_revenue,
                "remaining_stock": current_stock - quantity,
            }

        except sqlite3.Error as e:
            conn.rollback()
            return {"success": False, "error": f"Database transaction failed: {str(e)}"}

def record_tip(amount: float) -> Dict[str, Any]:
    """
    Records a customer tip or extra cash directly into the treasury and ledger.
    """
    if amount <= 0:
        return {"success": False, "error": "Tip amount must be greater than zero."}

    tip_amount = round(amount, 2)

    with get_connection() as conn:
        try:
            cursor = conn.cursor()

            # Credit treasury
            cursor.execute(
                "UPDATE treasury SET balance = balance + ? WHERE id = 1;",
                (tip_amount,),
            )

            # Insert as a SALE entry with SKU 'TIP'
            cursor.execute(
                """
                INSERT INTO ledger (entry_type, sku, quantity, unit_price, total_amount)
                VALUES ('SALE', 'TIP', 1, ?, ?);
                """,
                (tip_amount, tip_amount),
            )

            conn.commit()

            cursor.execute("SELECT balance FROM treasury WHERE id = 1;")
            new_balance = cursor.fetchone()["balance"]

            return {
                "success": True,
                "message": f"Recorded tip of ${tip_amount:.2f}.",
                "tip_amount": tip_amount,
                "new_balance": round(new_balance, 2),
            }

        except sqlite3.Error as e:
            conn.rollback()
            return {"success": False, "error": f"Database transaction failed: {str(e)}"}

def execute_restock(sku: str, quantity: int) -> Dict[str, Any]:
    """
    Executes a wholesale restock: checks treasury balance, debits wholesale cost,
    increments inventory stock, and writes an audit ledger record.
    """
    if quantity <= 0:
        return {"success": False, "error": "Quantity must be greater than zero."}

    with get_connection() as conn:
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT cost_price, name, stock FROM inventory WHERE sku = ?;", (sku,))
            item = cursor.fetchone()
            if not item:
                return {"success": False, "error": f"Item '{sku}' does not exist in catalog."}

            cost_price = item["cost_price"]
            total_expense = round(cost_price * quantity, 2)

            cursor.execute("SELECT balance FROM treasury WHERE id = 1;")
            current_balance = cursor.fetchone()["balance"]

            if current_balance < total_expense:
                return {
                    "success": False,
                    "error": f"Insufficient funds to restock '{sku}'. Needed ${total_expense:.2f}, balance is ${current_balance:.2f}.",
                }

            cursor.execute("UPDATE treasury SET balance = balance - ? WHERE id = 1;", (total_expense,))
            cursor.execute("UPDATE inventory SET stock = stock + ? WHERE sku = ?;", (quantity, sku))
            cursor.execute(
                """
                INSERT INTO ledger (entry_type, sku, quantity, unit_price, total_amount)
                VALUES ('RESTOCK', ?, ?, ?, ?);
                """,
                (sku, quantity, cost_price, total_expense),
            )

            conn.commit()
            return {
                "success": True,
                "message": f"Restocked {quantity}x {item['name']} for ${total_expense:.2f}.",
                "expense": total_expense,
                "new_stock": item["stock"] + quantity,
                "remaining_treasury": round(current_balance - total_expense, 2),
            }

        except sqlite3.Error as e:
            conn.rollback()
            return {"success": False, "error": f"Database transaction failed: {str(e)}"}
