"""
simulation.py - Autonomous multi-agent retail simulation:
CustomerAgent <-> SalesAgent <-> ProcurementAgent
"""

import sys
from pathlib import Path
import time

# Ensure the lemonade_stand folder is in sys.path for self-contained execution
STAND_DIR = Path(__file__).resolve().parent
if str(STAND_DIR) not in sys.path:
    sys.path.insert(0, str(STAND_DIR))

try:
    from agents.customer import CustomerAgent, SAMPLE_PERSONAS
    from agents.procurement import ProcurementAgent
    from agents.sales import SalesAgent
    from core.tools import get_inventory_status, get_recent_transactions, get_treasury_balance
except (ImportError, ModuleNotFoundError):
    from lemonade_stand.agents.customer import CustomerAgent, SAMPLE_PERSONAS
    from lemonade_stand.agents.procurement import ProcurementAgent
    from lemonade_stand.agents.sales import SalesAgent
    from lemonade_stand.core.tools import get_inventory_status, get_recent_transactions, get_treasury_balance



def conduct_customer_interaction(customer_profile: dict, sales_agent: SalesAgent, max_exchanges: int = 4):
    print(f"\n{'='*20} {customer_profile['name']} approaches {'='*20}", flush=True)
    print(f"Profile: {customer_profile['prompt']}", flush=True)

    customer = CustomerAgent(persona_prompt=customer_profile["prompt"])
    sales_agent.reset()

    # Customer initiates
    customer_utterance = customer.chat("Step up to the lemonade stand counter and greet the clerk.")

    for exchange in range(1, max_exchanges + 1):
        clean_customer_text = customer_utterance.replace("[DONE]", "").strip()
        print(f"\nCustomer: \"{clean_customer_text}\"", flush=True)

        # Let the salesperson answer/process the customer's statement
        time.sleep(4)
        sales_reply = sales_agent.chat(clean_customer_text)
        print(f"Sales Agent:\n{sales_reply}", flush=True)

        # If the customer had signaled they were leaving, terminate now
        if "[DONE]" in customer_utterance:
            print("[Customer leaves the counter]", flush=True)
            break

        time.sleep(4)
        customer_utterance = customer.chat(sales_reply)

    time.sleep(4)


def run_business_day():
    print("=" * 60, flush=True)
    print("            STARTING AUTONOMOUS BUSINESS DAY", flush=True)
    print("=" * 60, flush=True)

    start_cash = get_treasury_balance()
    print(f"\n[Morning Briefing] Starting Treasury: ${start_cash:.2f}", flush=True)

    sales_agent = SalesAgent()
    procurement_agent = ProcurementAgent()

    print("\n" + "#" * 40, flush=True)
    print(" PHASE 1: STORE DOORS OPEN (AI-TO-AI DIALOGUE)", flush=True)
    print("#" * 40, flush=True)

    # Simulate 3 autonomous customer visits
    for persona in SAMPLE_PERSONAS[:3]:
        conduct_customer_interaction(persona, sales_agent)

    print("\n" + "#" * 40, flush=True)
    print(" PHASE 2: CLOSING & INVENTORY AUDIT", flush=True)
    print("#" * 40, flush=True)

    audit_task = (
        "The store is now closed for the day. Inspect current stock levels. "
        "Any item with fewer than 10 units must be restocked back up to at least 20 units, "
        "provided we have sufficient treasury balance. Maintain a $10 cash cushion."
    )
    procurement_report = procurement_agent.run(audit_task)
    print(f"\n{procurement_report}", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("                 END OF DAY FINANCIAL REPORT", flush=True)
    print("=" * 60, flush=True)
    end_cash = get_treasury_balance()
    cash_diff = end_cash - start_cash
    print(f"Opening Treasury: ${start_cash:.2f}", flush=True)
    print(f"Closing Treasury: ${end_cash:.2f} (Net: {'+' if cash_diff >= 0 else ''}${cash_diff:.2f})", flush=True)

    print("\nCurrent Inventory:", flush=True)
    for item in get_inventory_status():
        print(f" - {item['name']} ({item['sku']}): {item['stock']} in stock", flush=True)

    print("\nLast 5 Transactions on the Ledger:", flush=True)
    for tx in get_recent_transactions(5):
        print(f" - [{tx['timestamp']}] {tx['entry_type']} | SKU: {tx['sku']} | Qty: {tx['quantity']} | Total: ${tx['total_amount']:.2f}", flush=True)


if __name__ == "__main__":
    run_business_day()