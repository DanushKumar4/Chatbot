"""Bank database operations layer.

Provides typed access to all banking tables through Supabase.
Side-effect operations (inserts, updates) go through the idempotency
layer when called from agent tools to ensure exactly-once execution.
"""

from typing import Optional
from app.database import supabase_admin
from app.domain import Customer, Account, Transaction, Loan, Card, Complaint


class BankDb:
    """Data access layer for the banking domain."""

    # ── Customers ──────────────────────────────────────────────

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        result = supabase_admin.table("customer").select("*").eq(
            "id", customer_id
        ).single().execute()
        if not result.data:
            return None
        d = result.data
        return Customer(
            id=d["id"], full_name=d["full_name"], email=d["email"],
            phone=d.get("phone"), pan_number=d.get("pan_number"),
            date_of_birth=d.get("date_of_birth"), address=d.get("address"),
        )

    # ── Accounts ───────────────────────────────────────────────

    def get_accounts(self, customer_id: int, status: str = "active") -> list[Account]:
        result = supabase_admin.table("account").select("*").eq(
            "customer_id", customer_id
        ).eq("status", status).execute()
        return [
            Account(
                id=a["id"], customer_id=a["customer_id"],
                account_number=a["account_number"],
                account_type=a["account_type"],
                balance=float(a["balance"]), status=a["status"],
            )
            for a in result.data
        ]

    def get_total_balance(self, customer_id: int) -> float:
        accounts = self.get_accounts(customer_id)
        return sum(a.balance for a in accounts)

    # ── Transactions ───────────────────────────────────────────

    def get_transactions(self, account_id: int, limit: int = 20) -> list[Transaction]:
        result = supabase_admin.table("transaction").select("*").eq(
            "account_id", account_id
        ).order("created_at", desc=True).limit(limit).execute()
        return [
            Transaction(
                id=t["id"], account_id=t["account_id"], txn_type=t["txn_type"],
                amount=float(t["amount"]), description=t.get("description"),
                reference_id=t.get("reference_id"),
            )
            for t in result.data
        ]

    def get_customer_transactions(self, customer_id: int, limit: int = 10) -> list[dict]:
        accounts = self.get_accounts(customer_id)
        account_ids = [a.id for a in accounts]
        account_map = {a.id: a.account_number for a in accounts}
        if not account_ids:
            return []
        result = supabase_admin.table("transaction").select("*").in_(
            "account_id", account_ids
        ).order("created_at", desc=True).limit(limit).execute()
        for t in result.data:
            t["account_number"] = account_map.get(t["account_id"], "Unknown")
        return result.data

    # ── Loans ──────────────────────────────────────────────────

    def get_loans(self, customer_id: int) -> list[Loan]:
        result = supabase_admin.table("loan").select("*").eq(
            "customer_id", customer_id
        ).order("applied_at", desc=True).execute()
        return [
            Loan(
                id=l["id"], customer_id=l["customer_id"],
                loan_type=l["loan_type"], principal=float(l["principal"]),
                interest_rate=float(l["interest_rate"]),
                tenure_months=l["tenure_months"],
                emi=float(l["emi"]) if l.get("emi") else None,
                status=l["status"],
            )
            for l in result.data
        ]

    def get_active_loan_exposure(self, customer_id: int) -> float:
        loans = self.get_loans(customer_id)
        return sum(l.principal for l in loans if l.status in ("approved", "disbursed"))

    def create_loan_application(self, customer_id: int, loan_type: str,
                                 principal: float, interest_rate: float,
                                 tenure_months: int, emi: float) -> dict:
        result = supabase_admin.table("loan").insert({
            "customer_id": customer_id,
            "loan_type": loan_type,
            "principal": principal,
            "interest_rate": interest_rate,
            "tenure_months": tenure_months,
            "emi": round(emi, 2),
            "status": "pending",
        }).execute()
        return result.data[0]

    # ── Cards ──────────────────────────────────────────────────

    def get_cards(self, customer_id: int) -> list[Card]:
        result = supabase_admin.table("card").select("*").eq(
            "customer_id", customer_id
        ).execute()
        return [
            Card(
                id=c["id"], customer_id=c["customer_id"],
                card_number=c["card_number"], card_type=c["card_type"],
                credit_limit=float(c["credit_limit"]) if c.get("credit_limit") else None,
                outstanding=float(c["outstanding"]) if c.get("outstanding") else None,
                status=c["status"], expiry_date=c["expiry_date"],
            )
            for c in result.data
        ]

    def get_card(self, card_id: int, customer_id: int) -> Optional[Card]:
        result = supabase_admin.table("card").select("*").eq(
            "id", card_id
        ).eq("customer_id", customer_id).single().execute()
        if not result.data:
            return None
        c = result.data
        return Card(
            id=c["id"], customer_id=c["customer_id"],
            card_number=c["card_number"], card_type=c["card_type"],
            credit_limit=float(c["credit_limit"]) if c.get("credit_limit") else None,
            outstanding=float(c["outstanding"]) if c.get("outstanding") else None,
            status=c["status"], expiry_date=c["expiry_date"],
        )

    def update_card_status(self, card_id: int, status: str) -> None:
        supabase_admin.table("card").update({"status": status}).eq(
            "id", card_id
        ).execute()

    # ── Complaints ─────────────────────────────────────────────

    def get_complaints(self, customer_id: int) -> list[Complaint]:
        result = supabase_admin.table("complaint").select("*").eq(
            "customer_id", customer_id
        ).order("created_at", desc=True).execute()
        return [
            Complaint(
                id=c["id"], customer_id=c["customer_id"],
                category=c["category"], subject=c["subject"],
                description=c["description"], status=c["status"],
                priority=c["priority"], resolution=c.get("resolution"),
            )
            for c in result.data
        ]

    def get_complaint(self, complaint_id: int, customer_id: int) -> Optional[Complaint]:
        result = supabase_admin.table("complaint").select("*").eq(
            "id", complaint_id
        ).eq("customer_id", customer_id).single().execute()
        if not result.data:
            return None
        c = result.data
        return Complaint(
            id=c["id"], customer_id=c["customer_id"],
            category=c["category"], subject=c["subject"],
            description=c["description"], status=c["status"],
            priority=c["priority"], resolution=c.get("resolution"),
        )

    def create_complaint(self, customer_id: int, category: str,
                          subject: str, description: str,
                          priority: str = "medium") -> dict:
        result = supabase_admin.table("complaint").insert({
            "customer_id": customer_id,
            "category": category,
            "subject": subject,
            "description": description,
            "priority": priority,
        }).execute()
        return result.data[0]

    def escalate_complaint(self, complaint_id: int) -> str:
        complaint = supabase_admin.table("complaint").select("priority").eq(
            "id", complaint_id
        ).single().execute()
        escalation = {"low": "medium", "medium": "high", "high": "critical", "critical": "critical"}
        new_priority = escalation[complaint.data["priority"]]
        supabase_admin.table("complaint").update(
            {"priority": new_priority}
        ).eq("id", complaint_id).execute()
        return new_priority
