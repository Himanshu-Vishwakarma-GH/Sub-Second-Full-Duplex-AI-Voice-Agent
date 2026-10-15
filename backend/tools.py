"""
Deterministic tool functions for the Voice Support Agent.
These tools are exposed to Groq Cloud LLM for function-calling.
"""

from typing import Dict, Any, Optional
from mock_data import ORDERS, CUSTOMERS, BRAND_INFO


def lookup_order(query: str) -> Dict[str, Any]:
    """
    Look up an order by order ID (e.g., 'ORD-101') or customer phone number (e.g., '9876543210').
    Returns order details, production stage, tracking status, and delivery estimates.
    """
    clean_query = query.strip().upper().replace(" ", "").replace("-", "")

    # 1. Search by exact or partial Order ID
    for oid, details in ORDERS.items():
        if oid.replace("-", "") == clean_query or oid == query.strip().upper():
            return {
                "found": True,
                "order_id": details["order_id"],
                "customer_name": details["customer_name"],
                "item_name": details["item_name"],
                "color": details["color"],
                "status": details["status"],
                "production_stage": details["production_stage"],
                "estimated_delivery": details.get("estimated_delivery") or details.get("delivery_date"),
                "shipping_address": details["shipping_address"],
                "tracking_carrier": details.get("tracking_carrier"),
                "tracking_number": details.get("tracking_number"),
                "alteration_eligible": details.get("is_alteration_eligible", False)
            }

    # 2. Search by phone number
    digits_only = "".join(filter(str.isdigit, query))
    if digits_only in CUSTOMERS:
        cust = CUSTOMERS[digits_only]
        order_list = []
        for oid in cust["order_ids"]:
            if oid in ORDERS:
                o = ORDERS[oid]
                order_list.append({
                    "order_id": o["order_id"],
                    "item_name": o["item_name"],
                    "status": o["status"],
                    "production_stage": o["production_stage"],
                    "estimated_delivery": o.get("estimated_delivery") or o.get("delivery_date")
                })
        return {
            "found": True,
            "customer_name": cust["name"],
            "phone": cust["phone"],
            "orders": order_list
        }

    return {
        "found": False,
        "message": f"No order or customer found for query '{query}'. Please ask for a valid Order ID (like ORD-101) or registered 10-digit phone number."
    }


def update_shipping_address(order_id: str, new_address: str) -> Dict[str, Any]:
    """
    Update delivery address for an order.
    Policy rule: Allowed only if order has not shipped or delivered yet.
    """
    clean_id = order_id.strip().upper()
    if clean_id not in ORDERS:
        return {
            "success": False,
            "message": f"Order {order_id} does not exist in our system."
        }

    order = ORDERS[clean_id]
    if order["status"] in ["SHIPPED", "DELIVERED"]:
        return {
            "success": False,
            "message": (
                f"Cannot update address for Order {clean_id} because it has already been {order['status'].lower()}. "
                f"Carrier is {order.get('tracking_carrier', 'our courier partner')}."
            )
        }

    # Execute update
    old_address = order["shipping_address"]
    order["shipping_address"] = new_address.strip()

    return {
        "success": True,
        "order_id": clean_id,
        "message": f"Shipping address for Order {clean_id} successfully updated to: '{new_address.strip()}'.",
        "previous_address": old_address
    }


def request_alteration(order_id: str, alteration_details: str) -> Dict[str, Any]:
    """
    Request a complimentary doorstep alteration for a delivered custom garment.
    Policy rule: Garment must be delivered and within 14-day alteration window.
    """
    clean_id = order_id.strip().upper()
    if clean_id not in ORDERS:
        return {
            "success": False,
            "message": f"Order {order_id} not found."
        }

    order = ORDERS[clean_id]
    if order["status"] != "DELIVERED":
        return {
            "success": False,
            "message": f"Order {clean_id} is currently '{order['status']}'. Alterations can only be requested after the garment has been delivered."
        }

    ticket_id = f"ALT-{clean_id.split('-')[-1]}01"
    order["alteration_ticket"] = {
        "ticket_id": ticket_id,
        "details": alteration_details,
        "status": "PICKUP_SCHEDULED",
        "pickup_window": "Within 24 to 48 hours"
    }

    return {
        "success": True,
        "ticket_id": ticket_id,
        "order_id": clean_id,
        "item": order["item_name"],
        "message": (
            f"Complimentary alteration ticket {ticket_id} logged for your {order['item_name']}. "
            f"Details: '{alteration_details}'. Our courier partner will pick up the garment from your address "
            f"within 24 to 48 hours for refitting by our master tailors."
        )
    }


def escalate_to_master_tailor(customer_name_or_phone: str, reason: str) -> Dict[str, Any]:
    """
    Escalate a complex bespoke issue, sizing dispute, or complaint to a human Master Tailor for callback.
    """
    return {
        "escalated": True,
        "case_id": "ESC-9092",
        "assigned_to": "Master Tailor Iqbal (Head of Bespoke Cutting)",
        "message": (
            f"Your request has been prioritized under Case ID ESC-9092. "
            f"Master Tailor Iqbal will call you back within 2 business hours regarding: {reason}."
        )
    }


# JSON Tool Schemas for Groq Function Calling
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by order ID (e.g. 'ORD-101') or 10-digit customer phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Order ID (like 'ORD-101') or 10-digit phone number (like '9876543210')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_shipping_address",
            "description": "Update the delivery address for an order before it has shipped.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The Order ID, e.g. 'ORD-101'"
                    },
                    "new_address": {
                        "type": "string",
                        "description": "The complete new shipping address"
                    }
                },
                "required": ["order_id", "new_address"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_alteration",
            "description": "Request a complimentary doorstep alteration for a delivered custom garment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The Order ID of the delivered item (e.g. 'ORD-103')"
                    },
                    "alteration_details": {
                        "type": "string",
                        "description": "Details of the fitting adjustment needed (e.g., 'Sleeves need shortening by 1 inch, chest is tight')"
                    }
                },
                "required": ["order_id", "alteration_details"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_master_tailor",
            "description": "Escalate to a human master tailor when customer has an unresolved dispute or complex custom fitting request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name_or_phone": {
                        "type": "string",
                        "description": "Customer name or phone number"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Summary of the issue or dispute"
                    }
                },
                "required": ["customer_name_or_phone", "reason"]
            }
        }
    }
]

# Dispatch map
TOOL_FUNCTIONS = {
    "lookup_order": lookup_order,
    "update_shipping_address": update_shipping_address,
    "request_alteration": request_alteration,
    "escalate_to_master_tailor": escalate_to_master_tailor
}
