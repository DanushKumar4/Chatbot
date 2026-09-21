from app.database import supabase_admin


class ComplaintTools:
    """Tools for complaint-related queries and operations."""

    def file_complaint(self, customer_id: int, category: str, subject: str, description: str, priority: str = "medium") -> dict:
        """File a new complaint for the customer.
        Use this when the customer wants to raise an issue or complaint about any banking service."""
        result = supabase_admin.table("complaint").insert({
            "customer_id": customer_id,
            "category": category,
            "subject": subject,
            "description": description,
            "priority": priority,
        }).execute()

        return {
            "success": True,
            "complaint_id": result.data[0]["id"],
            "message": f"Complaint #{result.data[0]['id']} filed successfully. Our team will look into it within 24-48 hours.",
        }

    def get_complaints(self, customer_id: int) -> dict:
        """Get all complaints filed by the customer.
        Use this when the customer asks about their complaint status."""
        complaints = supabase_admin.table("complaint").select("*").eq("customer_id", customer_id).order("created_at", desc=True).execute()
        return {"complaints": complaints.data, "count": len(complaints.data)}

    def get_complaint_detail(self, complaint_id: int, customer_id: int) -> dict:
        """Get detailed information about a specific complaint.
        Use this when the customer asks about a particular complaint by its ID."""
        complaint = supabase_admin.table("complaint").select("*").eq("id", complaint_id).eq("customer_id", customer_id).single().execute()
        if not complaint.data:
            return {"error": "Complaint not found or does not belong to this customer"}
        return {"complaint": complaint.data}

    def escalate_complaint(self, complaint_id: int, customer_id: int) -> dict:
        """Escalate a complaint to higher priority.
        Use this when the customer is dissatisfied with the resolution timeline or wants urgent attention."""
        complaint = supabase_admin.table("complaint").select("*").eq("id", complaint_id).eq("customer_id", customer_id).single().execute()
        if not complaint.data:
            return {"error": "Complaint not found"}

        priority_escalation = {"low": "medium", "medium": "high", "high": "critical", "critical": "critical"}
        new_priority = priority_escalation[complaint.data["priority"]]

        supabase_admin.table("complaint").update({"priority": new_priority}).eq("id", complaint_id).execute()
        return {
            "success": True,
            "message": f"Complaint #{complaint_id} escalated from {complaint.data['priority']} to {new_priority}. A senior representative will contact you within 12 hours.",
        }
