"""
Comprehensive company knowledge base articles for RAG vector search.
"""

DEFAULT_ARTICLES = [
    {
        "id": "KB-RET-01",
        "title": "30-Day Return and Refund Policy",
        "category": "Returns & Refunds",
        "content": (
            "ApexTech offers a 30-day hassle-free return policy for all standard purchases. "
            "To be eligible for a full refund, items must be in their original condition, with original packaging, "
            "accessories, and proof of purchase (order number). "
            "Return window: Customers have exactly 30 calendar days from the date of delivery to initiate a return. "
            "Refund method: Refunds are processed back to the original payment method within 3 to 5 business days "
            "after our warehouse inspects the returned item. "
            "Return shipping fee: Return shipping is free for VIP members or for defective/damaged items. "
            "For standard returns due to change of mind, a flat $5.99 return shipping label fee is deducted from the refund. "
            "Non-returnable items include gift cards, downloadable software licenses, and opened consumable items."
        )
    },
    {
        "id": "KB-SHIP-01",
        "title": "Shipping Methods, Costs, and Tracking Timelines",
        "category": "Shipping & Delivery",
        "content": (
            "ApexTech delivers to all 50 US states, Canada, and select international destinations. "
            "Shipping options: "
            "1. Standard Ground Shipping (3-5 business days): $4.99 or FREE on orders over $50. "
            "2. Expedited 2-Day Air (2 business days): $14.99. "
            "3. Overnight Priority (Next business day delivery): $24.99. "
            "Order processing: Orders placed before 2:00 PM EST Monday through Friday are dispatched the same day. "
            "Orders placed after 2:00 PM EST or on weekends are processed on the next business day. "
            "Tracking: Once shipped, customers receive an automated email containing their tracking number "
            "(FedEx, UPS, or DHL). Real-time tracking status can be queried directly via our support assistant."
        )
    },
    {
        "id": "KB-WAR-01",
        "title": "1-Year Limited Manufacturer Warranty & Hardware Defect Claims",
        "category": "Warranty & Repairs",
        "content": (
            "All ApexTech branded hardware products include a 1-Year Limited Manufacturer Warranty covering defects in materials "
            "and workmanship under normal consumer use. "
            "Coverage: The warranty covers hardware failures, internal component defects, and power supply malfunctions. "
            "Exclusions: The warranty does not cover accidental damage, drops, water immersion, cosmetic wear and tear, "
            "or unauthorized repairs. "
            "Claim procedure: If your item is older than the 30-day return window but within 12 months of purchase, "
            "you can initiate a warranty replacement claim. Support agents or our AI assistant will verify your purchase "
            "date and provide a prepaid return label for repair or replacement."
        )
    },
    {
        "id": "KB-ORD-01",
        "title": "Order Cancellation and Modification Guidelines",
        "category": "Order Management",
        "content": (
            "You can cancel or modify an order only while it is in 'Processing' status. "
            "Once an order transitions to 'In Transit' or 'Shipped', it cannot be cancelled or re-routed, "
            "because it has already departed the fulfillment facility. "
            "To cancel an order in 'Processing' status, provide your order ID to our support agent. "
            "If the order has already shipped, you can simply wait for delivery and initiate a standard 30-day return."
        )
    },
    {
        "id": "KB-SEC-01",
        "title": "Account Security, Two-Factor Authentication (2FA) and Password Recovery",
        "category": "Account & Security",
        "content": (
            "We take security seriously. You can secure your ApexTech account using Two-Factor Authentication (2FA) via SMS or authenticator apps (Google Authenticator, Authy). "
            "Password Reset: Click 'Forgot Password' on the login screen to receive a secure 6-digit verification code. "
            "Suspicious Activity: If you suspect unauthorized access to your account or payment cards, immediately contact support "
            "or request human agent escalation. Our team can lock your account credentials and cancel unauthorized orders."
        )
    },
    {
        "id": "KB-ESC-01",
        "title": "Customer Support Escalation and Human Agent Protocol",
        "category": "Support Policies",
        "content": (
            "Customers may request to speak with a human support specialist at any point during a conversation. "
            "Our AI Support Agent is empowered to resolve common inquiries (order tracking, standard returns, FAQs, and ticket creation). "
            "However, the AI will immediately escalate to a human tier-2 supervisor if: "
            "1. The customer explicitly asks to speak to a human or representative. "
            "2. Repeated dissatisfaction or high sentiment frustration is detected. "
            "3. The inquiry involves complex billing disputes, fraud reports, or custom commercial quotes. "
            "Human specialists are available Monday through Friday 8 AM - 8 PM EST. "
            "Escalated tickets receive a priority response within 2 hours."
        )
    },
    {
        "id": "KB-FLIP-01",
        "title": "Flipkart 7-Day Replacement Policy & Ekart Logistics Tracking",
        "category": "Flipkart Marketplace",
        "content": (
            "For all orders purchased on Flipkart India (e.g. mobile phones, smartwatches, electronics, and fashion): "
            "1. Tracking: Shipped via Ekart Logistics with tracking format FMPC... Real-time delivery status, local delivery hub, "
            "and out-for-delivery OTP are provided directly. "
            "2. 7-Day Replacement: Electronics and smartphones have a 7-day replacement window for defective, damaged, or dead-on-arrival items. "
            "3. Delivery OTP: Customers must provide the 4-digit secret delivery OTP to the Ekart delivery executive at the time of delivery. "
            "4. Returns & Refunds: Refunds for prepaid UPI/Cards are returned within 24-48 hours after courier pickup."
        )
    },
    {
        "id": "KB-AMZ-01",
        "title": "Amazon Multi-Platform Order Verification and Return Guidelines",
        "category": "Amazon Marketplace",
        "content": (
            "For orders fulfilled through Amazon.in or Amazon Global: "
            "1. Order format: 17-digit format (e.g. 171-8839201-9921). "
            "2. Shipping: Handled by Amazon Transportation Services (ATS). "
            "3. Tracking & Invoices: Live delivery window and GST tax invoices are available upon providing the Amazon Order ID."
        )
    }
]
