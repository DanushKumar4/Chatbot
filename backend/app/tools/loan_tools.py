from app.database import supabase_admin


class LoanTools:
    """Tools for loan-related queries and operations."""

    def check_loan_eligibility(self, customer_id: int, loan_type: str, amount: float) -> dict:
        """Check if a customer is eligible for a loan based on their profile and existing loans.
        Use this when the customer asks about loan eligibility or wants to know if they qualify."""
        customer = supabase_admin.table("customer").select("*").eq("id", customer_id).single().execute()
        if not customer.data:
            return {"eligible": False, "reason": "Customer not found"}

        existing = supabase_admin.table("loan").select("*").eq("customer_id", customer_id).in_("status", ["approved", "disbursed"]).execute()
        total_active = sum(l["principal"] for l in existing.data)

        accounts = supabase_admin.table("account").select("balance").eq("customer_id", customer_id).execute()
        total_balance = sum(a["balance"] for a in accounts.data)

        max_allowed = total_balance * 10
        if total_active + amount > max_allowed:
            return {
                "eligible": False,
                "reason": f"Total loan exposure would exceed limit. Current active loans: ₹{total_active:,.2f}, max allowed: ₹{max_allowed:,.2f}",
            }

        rates = {"home": 8.5, "personal": 12.0, "car": 9.5, "education": 9.0}
        rate = rates.get(loan_type, 12.0)

        return {
            "eligible": True,
            "loan_type": loan_type,
            "amount": amount,
            "interest_rate": rate,
            "max_tenure_months": 240 if loan_type == "home" else 60,
            "estimated_emi": round(amount * rate / 100 / 12 * (1 + rate / 100 / 12) ** 60 / ((1 + rate / 100 / 12) ** 60 - 1), 2),
        }

    def calculate_emi(self, principal: float, rate: float, tenure_months: int) -> dict:
        """Calculate EMI for a given principal, interest rate, and tenure.
        Use this when the customer asks about EMI calculation or monthly payments."""
        monthly_rate = rate / 100 / 12
        if monthly_rate == 0:
            emi = principal / tenure_months
        else:
            emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        total_payment = emi * tenure_months
        total_interest = total_payment - principal

        return {
            "emi": round(emi, 2),
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
            "principal": principal,
            "rate": rate,
            "tenure_months": tenure_months,
        }

    def apply_for_loan(self, customer_id: int, loan_type: str, amount: float, tenure_months: int) -> dict:
        """Submit a loan application for a customer.
        Use this when the customer confirms they want to apply for a loan after checking eligibility."""
        rates = {"home": 8.5, "personal": 12.0, "car": 9.5, "education": 9.0}
        rate = rates.get(loan_type, 12.0)
        monthly_rate = rate / 100 / 12
        emi = amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)

        result = supabase_admin.table("loan").insert({
            "customer_id": customer_id,
            "loan_type": loan_type,
            "principal": amount,
            "interest_rate": rate,
            "tenure_months": tenure_months,
            "emi": round(emi, 2),
            "status": "pending",
        }).execute()

        return {
            "success": True,
            "loan_id": result.data[0]["id"],
            "message": f"Loan application submitted. Loan ID: {result.data[0]['id']}. EMI: ₹{round(emi, 2):,.2f}/month",
        }

    def get_loan_status(self, customer_id: int) -> dict:
        """Get all loans for a customer with their current status.
        Use this when the customer asks about their loan status or loan details."""
        loans = supabase_admin.table("loan").select("*").eq("customer_id", customer_id).order("applied_at", desc=True).execute()
        return {"loans": loans.data, "count": len(loans.data)}
