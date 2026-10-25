import json
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

@dataclass
class Customer:
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    tier: str = "Standard"
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Order:
    id: str
    customer_id: str
    items: str  # JSON or comma-separated string
    total_amount: float
    currency: str = "USD"
    status: str = "Processing"
    shipping_carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    order_date: str = ""
    is_refundable: int = 1

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        try:
            d["items_parsed"] = json.loads(self.items) if isinstance(self.items, str) and (self.items.startswith("[") or self.items.startswith("{")) else self.items
        except Exception:
            d["items_parsed"] = self.items
        return d

@dataclass
class Ticket:
    id: str
    subject: str
    description: str
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    priority: str = "MEDIUM"
    status: str = "OPEN"
    assigned_agent: str = "AI Agent"
    resolution_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ChatMessage:
    session_id: str
    role: str
    content: str
    tool_calls: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.tool_calls:
            try:
                d["tool_calls_parsed"] = json.loads(self.tool_calls)
            except Exception:
                d["tool_calls_parsed"] = self.tool_calls
        return d
