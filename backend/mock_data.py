"""
Mock database and brand policy rules for a custom bespoke clothing brand: "Verve Bespoke Atelier".
Tailored for voice agent tool-calling, order lookup, address modifications, and alteration requests.
"""

BRAND_INFO = {
    "name": "Verve Bespoke Atelier",
    "specialty": "Made-to-measure custom suits, shirts, blazers, and ethnic wear",
    "turnaround_time": "7-10 business days for handcrafted tailoring",
    "alteration_policy": (
        "All custom-tailored garments are made strictly to customer measurements and are non-refundable. "
        "However, we provide ONE complimentary alteration within 14 days of delivery. "
        "Return pickups for alterations are arranged free of cost."
    ),
    "cancellation_policy": (
        "Orders can only be canceled or modified before the fabric has been cut. "
        "Once an order enters 'IN_PRODUCTION' (fabric cutting), cancellation is not permitted."
    ),
    "address_change_policy": (
        "Delivery address can be updated anytime before the order status is marked as 'SHIPPED'."
    )
}

CUSTOMERS = {
    "9876543210": {
        "id": "CUST-001",
        "name": "Rahul Sharma",
        "email": "rahul.sharma@example.com",
        "phone": "9876543210",
        "city": "Bengaluru",
        "saved_measurements": {
            "chest_inches": 40.5,
            "shoulder_inches": 18.0,
            "sleeve_length_inches": 25.0,
            "waist_inches": 34.0,
            "fit_preference": "Slim Contemporary"
        },
        "order_ids": ["ORD-101"]
    },
    "9811223344": {
        "id": "CUST-002",
        "name": "Ananya Iyer",
        "email": "ananya.iyer@example.com",
        "phone": "9811223344",
        "city": "Mumbai",
        "saved_measurements": {
            "bust_inches": 36.0,
            "waist_inches": 28.0,
            "hip_inches": 38.0,
            "height": "5ft 6in",
            "fit_preference": "Tailored Elegant"
        },
        "order_ids": ["ORD-102"]
    },
    "9988776655": {
        "id": "CUST-003",
        "name": "Vikram Malhotra",
        "email": "vikram.m@example.com",
        "phone": "9988776655",
        "city": "Delhi NCR",
        "saved_measurements": {
            "chest_inches": 42.0,
            "collar_inches": 16.5,
            "sleeve_length_inches": 26.0,
            "fit_preference": "Classic Regular"
        },
        "order_ids": ["ORD-103"]
    },
    "9123456789": {
        "id": "CUST-004",
        "name": "Pooja Mehta",
        "email": "pooja.mehta@example.com",
        "phone": "9123456789",
        "city": "Hyderabad",
        "saved_measurements": {
            "waist_inches": 30.0,
            "inseam_inches": 29.5,
            "fit_preference": "Relaxed High-Rise"
        },
        "order_ids": ["ORD-104"]
    }
}

ORDERS = {
    "ORD-101": {
        "order_id": "ORD-101",
        "customer_phone": "9876543210",
        "customer_name": "Rahul Sharma",
        "item_name": "Bespoke Super-120s Italian Wool Blazer",
        "color": "Midnight Navy",
        "custom_specs": "Double-vent, notch lapel, horn buttons, monogram 'RS' on inner pocket",
        "price": 14999,
        "status": "IN_PRODUCTION",
        "production_stage": "Hand-stitching and lining assembly by Master Tailor Iqbal",
        "estimated_completion": "In 3 business days",
        "estimated_delivery": "Within 5 business days",
        "shipping_address": "Flat 402, Green Glen Layout, Bellandur, Bengaluru - 560103",
        "tracking_carrier": None,
        "tracking_number": None,
        "is_alteration_eligible": False
    },
    "ORD-102": {
        "order_id": "ORD-102",
        "customer_phone": "9811223344",
        "customer_name": "Ananya Iyer",
        "item_name": "Handcrafted Chanderi Silk Kurta Set",
        "color": "Emerald Green with Zari accents",
        "custom_specs": "Mandarin collar, customized 3/4 sleeves, pocket lining",
        "price": 8499,
        "status": "SHIPPED",
        "production_stage": "Completed & Quality Passed",
        "estimated_delivery": "Expected TODAY by 7:00 PM",
        "shipping_address": "B-12 Sea View Apartments, Worli, Mumbai - 400018",
        "tracking_carrier": "BlueDart Express",
        "tracking_number": "BD-88392019",
        "is_alteration_eligible": False
    },
    "ORD-103": {
        "order_id": "ORD-103",
        "customer_phone": "9988776655",
        "customer_name": "Vikram Malhotra",
        "item_name": "Custom Tailored Egyptian Cotton Tuxedo Shirt",
        "color": "Crisp White",
        "custom_specs": "French cuffs, pleated bib front, mother-of-pearl buttons",
        "price": 4299,
        "status": "DELIVERED",
        "production_stage": "Completed",
        "delivery_date": "Delivered 2 days ago",
        "shipping_address": "House 14, Sector 15, Gurgaon - 122001",
        "tracking_carrier": "Delhivery",
        "tracking_number": "DEL-44910283",
        "is_alteration_eligible": True,
        "alteration_ticket": None
    },
    "ORD-104": {
        "order_id": "ORD-104",
        "customer_phone": "9123456789",
        "customer_name": "Pooja Mehta",
        "item_name": "Bespoke Irish Linen Summer Trousers",
        "color": "Sand Beige",
        "custom_specs": "Side adjusters (no belt loops), cuffed hems (1.5 inch)",
        "price": 5499,
        "status": "AWAITING_MEASUREMENT_CONFIRMATION",
        "production_stage": "Fabric reserved, awaiting final waist confirmation",
        "estimated_delivery": "7 days after confirmation",
        "shipping_address": "Road No. 36, Jubilee Hills, Hyderabad - 500033",
        "tracking_carrier": None,
        "tracking_number": None,
        "is_alteration_eligible": False
    }
}
