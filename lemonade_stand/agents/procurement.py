from agents.base import BaseAgent
from core.tools import (
    execute_restock,
    get_inventory_status,
    get_treasury_balance,
)

PROCUREMENT_SYSTEM_INSTRUCTION = r"""
You are the Inventory & Procurement Manager for the Lemonade Stand.
Your responsibility is to ensure the store never runs out of stock while keeping spending within available cash reserves.

Operational Rules:
1. Always begin by inspecting inventory levels via `get_inventory_status` and available cash via `get_treasury_balance`.
2. Reorder Rules:
   - Identify any SKU where `stock` has dropped below the reorder threshold (default: less than 10 units).
   - If multiple items are low, prioritize higher-margin or primary items (e.g., LEMON_CUP).
   - Calculate how many units to purchase so that total expense does NOT exceed current treasury balance. Leave a small cash cushion (at least \$10.00).
   - Call `execute_restock` with the SKU and chosen quantity.
3. If an item cannot be restocked due to insufficient funds:
   - State the issue clearly.
   - Do NOT execute restock calls that exceed available funds.
4. Conclude with a concise operational report outlining restock actions taken, costs incurred, and remaining cash.
"""


class ProcurementAgent(BaseAgent):
    def __init__(self, model: str = "gemini-3.5-flash-lite"):
        super().__init__(
            name="ProcurementAgent",
            system_instruction=PROCUREMENT_SYSTEM_INSTRUCTION,
            tools=[get_inventory_status, get_treasury_balance, execute_restock],
            model=model,
        )


# -------------------------------------------------------------
# Standalone Test
# -------------------------------------------------------------
if __name__ == "__main__":
    agent = ProcurementAgent()

    test_prompt = "Run our end-of-day inventory audit. Check stock levels and restock anything running low if funds allow."
    report = agent.run(test_prompt)

    print("=" * 50)
    print("PROCUREMENT REPORT:")
    print(report)