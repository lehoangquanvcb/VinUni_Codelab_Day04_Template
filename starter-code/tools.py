
import json
import os
from typing import List, Dict, Any
from datetime import datetime

RAW_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "raw-data"
)


# =========================================================
# TOOL 1: SEARCH PRODUCT CATALOG
# Slide 14
# =========================================================

def search_product_catalog(
    category: str,
    max_price: int = 999999999999
) -> List[Dict[str, Any]]:
    """
    Tra cứu sản phẩm/dịch vụ Vingroup theo danh mục và giá tối đa.
    """

    catalog_file = os.path.join(
        RAW_DATA_DIR, "product_catalog.json"
    )

    if not os.path.exists(catalog_file):
        return [{"error": "Product catalog file not found."}]

    with open(catalog_file, "r", encoding="utf-8") as f:
        products = json.load(f)

    results = [
        p for p in products
        if p["category"].lower() == category.lower()
        and p["price_vnd"] <= max_price
    ]

    return results


# =========================================================
# TOOL 2: SUBMIT SUPPORT TICKET
# Slide 15
# =========================================================

def submit_support_ticket(
    customer_name: str,
    issue_description: str,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Ghi nhận yêu cầu hỗ trợ khách hàng.
    """

    tickets_file = os.path.join(
        RAW_DATA_DIR, "support_tickets.json"
    )

    existing_tickets = []

    if os.path.exists(tickets_file):
        with open(tickets_file, "r", encoding="utf-8") as f:
            existing_tickets = json.load(f)

    today = datetime.now().strftime("%Y%m%d")
    seq = len(existing_tickets) + 1
    ticket_id = f"TK-{today}-{seq:03d}"

    new_ticket = {
        "ticket_id": ticket_id,
        "customer_name": customer_name,
        "issue_description": issue_description,
        "priority": priority.lower(),
        "status": "open",
        "created_at": datetime.now().astimezone().isoformat(),
        "category": "general"
    }

    existing_tickets.append(new_ticket)

    with open(tickets_file, "w", encoding="utf-8") as f:
        json.dump(
            existing_tickets,
            f,
            indent=2,
            ensure_ascii=False
        )

    return {
        "ticket_id": ticket_id,
        "customer_name": customer_name,
        "priority": priority.lower(),
        "status": "open",
        "message": (
            f"Ticket {ticket_id} đã được tạo thành công "
            f"cho khách hàng {customer_name}."
        )
    }


# =========================================================
# TOOL DEFINITIONS - JSON SCHEMAS
# Slide 16
# =========================================================

TOOL_DEFINITIONS = [
    {
        "name": "search_product_catalog",
        "description": (
            "Tra cứu sản phẩm/dịch vụ Vingroup "
            "(xe điện VinFast, resort Vinpearl) "
            "theo danh mục và giá tối đa."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": (
                        "Loại sản phẩm: xe_dien hoặc du_lich."
                    ),
                    "enum": ["xe_dien", "du_lich"]
                },
                "max_price": {
                    "type": "integer",
                    "description": "Giá tối đa tính bằng VNĐ."
                }
            },
            "required": ["category"]
        }
    },
    {
        "name": "submit_support_ticket",
        "description": (
            "Ghi nhận yêu cầu hỗ trợ khách hàng "
            "khi có lỗi, khiếu nại hoặc phản hồi."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Họ tên khách hàng."
                },
                "issue_description": {
                    "type": "string",
                    "description": "Mô tả vấn đề cần hỗ trợ."
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                    "description": "Mức độ ưu tiên."
                }
            },
            "required": [
                "customer_name",
                "issue_description"
            ]
        }
    }
]


# =========================================================
# TOOL MAP
# =========================================================

TOOL_MAP = {
    "search_product_catalog": search_product_catalog,
    "submit_support_ticket": submit_support_ticket
}
