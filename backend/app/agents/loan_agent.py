from app.agents.base import BaseAgent
from app.tools.loan_tools import LoanTools


class LoanAgent(BaseAgent):
    name = "loan_agent"
    system_prompt = (
        "You are the Loan Specialist at SmartBank. You help customer (ID: {customer_id}) with:\n"
        "- Checking loan eligibility\n"
        "- Calculating EMI for different loan types\n"
        "- Submitting loan applications\n"
        "- Checking loan status\n\n"
        "Available loan types: home, personal, car, education.\n"
        "Always use the tools to fetch real data. Never make up numbers.\n"
        "Be professional but friendly. Use ₹ for currency."
    )
    tool_instance = LoanTools()
