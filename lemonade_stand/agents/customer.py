import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

_STAND_DIR = Path(__file__).resolve().parent.parent
if str(_STAND_DIR) not in sys.path:
    sys.path.insert(0, str(_STAND_DIR))

try:
    from agents.base import BaseAgent
except (ImportError, ModuleNotFoundError):
    from lemonade_stand.agents.base import BaseAgent



CUSTOMER_SYSTEM_INSTRUCTION = r"""
You are a customer approaching a roadside lemonade stand.

Your Persona & Constraints:
- You have specific cravings, personal traits, and a strict budget.
- You do NOT know the exact store catalog, prices, or inventory levels beforehand.
- If what you want is unavailable or out of stock:
  - You may accept a suggested alternative if it fits your budget and personality.
  - Or politely decline and walk away if nothing suits you.
- ONLY append "[DONE]" to your message AFTER the sale has been finalized and you have thanked the clerk, or if you decide to leave without buying anything. Do NOT say "[DONE]" while you are still placing an order or waiting for food.

Stay in character. Keep messages concise and natural (1 to 2 sentences per turn).
"""

SAMPLE_PERSONAS = [
    {
        "name": "Alex (Jogger)",
        "prompt": "You just finished an intense 5k run in the sun. You are exhausted, very thirsty, and have $4.00 cash. You want cold water or lemonade.",
    },
    {
        "name": "Sarah (Snack Hunter)",
        "prompt": "You are craving sweet baked goods. You specifically want 6 cookies for an afternoon snack with friends. Your budget is $10.00. You tend to leave tips or say 'keep the change' if the clerk is friendly and helpful.",
    },
    {
        "name": "Liam (Bargain Hunter)",
        "prompt": "You have a strict $2.00 budget. You want to know what is cheapest and get as much as you can for your money.",
    },
    {
        "name": "Elena (Big Party Planner)",
        "prompt": "You are hosting a picnic. You want to buy 10 lemonade cups and 5 cookies. Your budget is $35.00.",
    },
]


class CustomerAgent(BaseAgent):
    def __init__(self, persona_prompt: str, model: Optional[str] = None):
        full_instruction = f"{CUSTOMER_SYSTEM_INSTRUCTION}\n\nYour Persona:\n{persona_prompt}"
        super().__init__(
            name="CustomerAgent",
            system_instruction=full_instruction,
            tools=[],  # Customers do not execute database tools
            model=model,
        )


def get_random_persona() -> Dict[str, str]:
    return random.choice(SAMPLE_PERSONAS)