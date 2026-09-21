from app.database import supabase_admin


class AccountTools:
    """Tools for account-related queries and operations."""

    def get_account_balance(self, customer_id: int) -> dict:
        """Get all account balances for a customer.
        Use this when the customer asks about their balance or account details."""
        accounts = supabase_admin.table("account").select("*").eq("customer_id", customer_id).eq("status", "active").execute()
        return {
            "accounts": [
                {
                    "account_number": a["account_number"],
                    "type": a["account_type"],
                    "balance": a["balance"],
                }
                for a in accounts.data
            ],
            "total_balance": sum(a["balance"] for a in accounts.data),
        }

    def get_recent_transactions(self, customer_id: int, limit: int = 10) -> dict:
        """Get recent transactions across all accounts of a customer.
        Use this when the customer asks about recent transactions or account activity."""
        accounts = supabase_admin.table("account").select("id, account_number").eq("customer_id", customer_id).execute()
        account_ids = [a["id"] for a in accounts.data]
        account_map = {a["id"]: a["account_number"] for a in accounts.data}

        if not account_ids:
            return {"transactions": [], "message": "No accounts found"}

        txns = supabase_admin.table("transaction").select("*").in_("account_id", account_ids).order("created_at", desc=True).limit(limit).execute()
        for t in txns.data:
            t["account_number"] = account_map.get(t["account_id"], "Unknown")
        return {"transactions": txns.data, "count": len(txns.data)}

    def get_account_statement(self, account_id: int, limit: int = 20) -> dict:
        """Get a mini-statement for a specific account.
        Use this when the customer asks for a statement of a particular account."""
        account = supabase_admin.table("account").select("*").eq("id", account_id).single().execute()
        if not account.data:
            return {"error": "Account not found"}

        txns = supabase_admin.table("transaction").select("*").eq("account_id", account_id).order("created_at", desc=True).limit(limit).execute()
        return {
            "account": {
                "number": account.data["account_number"],
                "type": account.data["account_type"],
                "balance": account.data["balance"],
            },
            "transactions": txns.data,
        }

    def get_customer_profile(self, customer_id: int) -> dict:
        """Get customer profile information.
        Use this when the customer asks about their profile or personal details."""
        customer = supabase_admin.table("customer").select("id, full_name, email, phone, address, created_at").eq("id", customer_id).single().execute()
        if not customer.data:
            return {"error": "Customer not found"}
        return {"customer": customer.data}
