import sys
from pathlib import Path

_STAND_DIR = Path(__file__).resolve().parent.parent
if str(_STAND_DIR) not in sys.path:
    sys.path.insert(0, str(_STAND_DIR))

try:
    from agents.base import BaseAgent
    from core.tools import execute_sale, get_inventory_status, record_tip
except (ImportError, ModuleNotFoundError):
    from lemonade_stand.agents.base import BaseAgent
    from lemonade_stand.core.tools import execute_sale, get_inventory_status, record_tip



SALES_SYSTEM_INSTRUCTION = r"""
You are the Point of Sale (POS) and Customer Service representative for the Lemonade Stand.
Your goal is to assist customers, answer product and pricing questions, and process confirmed sales.

Operational Rules & Protocol:
1. Always check current inventory using `get_inventory_status` before stating availability or pricing.
2. STRICT PRICING & NO HAGGLING:
   - Prices are 100% fixed as listed in the catalog. You cannot offer discounts, bundle deals, or accept lower offers under any circumstances.
   - If a customer tries to negotiate, haggle, or asks for more than their budget allows (e.g., asking for a \$1.50 cookie + \$1.00 water for \$2.00):
     Politely decline the discount, explain that the total is \$2.50, and ask which single item they would like instead to stay within their budget.
3. Order Confirmation Protocol:
   - INQUIRIES: Answer politely with available quantities and prices. Do not charge yet.
   - SHORTAGES: If stock is insufficient, state available quantity and ask before selling.
   - EXPLICIT ORDERS: Call `execute_sale` when the customer clearly agrees to purchase items they can afford.
4. Response Style:
   - Always reply in plain English.
   - Keep answers warm, concise, and clear.
5. CASH AND CHANGE:
   - When a customer hands over cash larger than the purchase price (e.g., "Here is \$4.00" for a \$2.50 drink): Calculate and return the correct change (\$1.50). 
   - DO NOT call `record_tip` unless the customer EXPLICITLY says "keep the change" or suggests that they are tipping you. 
   - Handing over larger bills is standard payment, not an assumed tip.
"""


from typing import Optional


class SalesAgent(BaseAgent):
    def __init__(self, model: Optional[str] = None):
        super().__init__(
            name="SalesAgent",
            system_instruction=SALES_SYSTEM_INSTRUCTION,
            tools=[get_inventory_status, execute_sale, record_tip],
            model=model,
        )


if __name__ == "__main__":
    import time

    agent = SalesAgent()

    print("\n--- Multi-Turn Customer Scenario Test ---")

    # Turn 1: Customer asks about stock (should NOT trigger execute_sale)
    user_turn_1 = "Hi! Do you have 25 cookies for an office party?"
    print(f"\nCustomer: {user_turn_1}")
    reply_1 = agent.chat(user_turn_1)
    print(f"SalesAgent: {reply_1}")

    time.sleep(2)

    # Turn 2: Customer agrees to whatever is available (SHOULD trigger execute_sale)
    user_turn_2 = "Ah bummer. How about whatever you have left? I'll take all of them."
    print(f"\nCustomer: {user_turn_2}")
    reply_2 = agent.chat(user_turn_2)
    print(f"SalesAgent: {reply_2}")