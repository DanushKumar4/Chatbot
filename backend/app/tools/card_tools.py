from app.database import supabase_admin


class CardTools:
    """Tools for card-related queries and operations."""

    def get_cards(self, customer_id: int) -> dict:
        """Get all cards for a customer with their details.
        Use this when the customer asks about their cards."""
        cards = supabase_admin.table("card").select("*").eq("customer_id", customer_id).execute()
        return {
            "cards": [
                {
                    "id": c["id"],
                    "card_number": c["card_number"],
                    "type": c["card_type"],
                    "status": c["status"],
                    "credit_limit": c.get("credit_limit"),
                    "outstanding": c.get("outstanding"),
                    "expiry_date": c["expiry_date"],
                }
                for c in cards.data
            ],
            "count": len(cards.data),
        }

    def block_card(self, card_id: int, customer_id: int) -> dict:
        """Block a card immediately. Use this when the customer reports a lost/stolen card
        or wants to block their card for security reasons."""
        card = supabase_admin.table("card").select("*").eq("id", card_id).eq("customer_id", customer_id).single().execute()
        if not card.data:
            return {"success": False, "message": "Card not found or does not belong to this customer"}
        if card.data["status"] == "blocked":
            return {"success": False, "message": "Card is already blocked"}

        supabase_admin.table("card").update({"status": "blocked"}).eq("id", card_id).execute()
        return {
            "success": True,
            "message": f"Card {card.data['card_number']} has been blocked successfully. Please visit your nearest branch for a replacement.",
        }

    def unblock_card(self, card_id: int, customer_id: int) -> dict:
        """Unblock a previously blocked card. Use this when the customer wants to
        reactivate their blocked card."""
        card = supabase_admin.table("card").select("*").eq("id", card_id).eq("customer_id", customer_id).single().execute()
        if not card.data:
            return {"success": False, "message": "Card not found or does not belong to this customer"}
        if card.data["status"] != "blocked":
            return {"success": False, "message": f"Card is currently {card.data['status']}, not blocked"}

        supabase_admin.table("card").update({"status": "active"}).eq("id", card_id).execute()
        return {"success": True, "message": f"Card {card.data['card_number']} has been unblocked and is now active."}

    def get_card_statement(self, card_id: int, customer_id: int) -> dict:
        """Get outstanding balance and credit limit details for a credit card.
        Use this when the customer asks about their credit card bill or outstanding amount."""
        card = supabase_admin.table("card").select("*").eq("id", card_id).eq("customer_id", customer_id).single().execute()
        if not card.data:
            return {"error": "Card not found"}
        if card.data["card_type"] != "credit":
            return {"message": "This is a debit card — no outstanding balance or credit limit applies."}

        return {
            "card_number": card.data["card_number"],
            "credit_limit": card.data["credit_limit"],
            "outstanding": card.data["outstanding"],
            "available_credit": card.data["credit_limit"] - (card.data["outstanding"] or 0),
        }
