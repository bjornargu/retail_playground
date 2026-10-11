## Overview

An autonomous, multi-agent retail simulation ("Lemonade Stand") built with Python, SQLite, and the Google GenAI SDK (`gemini-3.5-flash-lite`). 

The system models a complete daily business cycle featuring state-aware, multi-turn dialogues between independent agents:
- **SalesAgent:** Handles customer inquiries, fixed-price retail policies, order confirmations, and cash/tip accounting.
- **CustomerAgent:** Generates persona-driven buyer behavior with distinct cravings, strict budgets, and adaptive negotiation.
- **ProcurementAgent:** Performs end-of-day stock audits and automated restocking against a cash cushion.

### Key Architecture
- **Strict ACID State:** SQLite-backed treasury, catalog, and an immutable audit ledger with foreign-key and constraint validation.
- **Manual Tool Orchestration:** Explicit inspect-and-execute tool loops (`disable=True` on automatic calling) for full observability.
- **Resilient Rate-Limiting:** Dynamic exponential backoff that parses server retry delays to safely run complex simulations within free-tier quotas (15 RPM).