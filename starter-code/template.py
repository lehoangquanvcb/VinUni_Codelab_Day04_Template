"""VinUni Day 04 — mock Tool Calling Agent."""
import json
import re
from typing import Any, Dict, List
from tools import TOOL_MAP, TOOL_DEFINITIONS

SYSTEM_PROMPT = """
PERSONA: Bạn là VinAssistant, trợ lý tư vấn sản phẩm Vingroup, lịch sự và chính xác.
AVAILABLE TOOLS: search_product_catalog để tra cứu xe VinFast và Vinpearl;
submit_support_ticket để ghi nhận khiếu nại, phản hồi.
CORE RULES: Không bịa giá, tính năng, tồn kho hoặc ticket_id. Dùng tool
khi cần tra cứu sản phẩm hoặc tạo ticket. Có thể gọi nhiều tool trong một yêu cầu.
OPERATIONAL BOUNDARIES: Chỉ hỗ trợ sản phẩm và dịch vụ Vingroup.
OUTPUT CONTRACT: Trả lời tiếng Việt, rõ sản phẩm/giá hoặc ticket_id.
Thought/Action/Observation được ghi trong trace; người dùng chỉ nhận Final Answer.
"""

class ChatbotBaseline:
    """Chatbot giả lập không gọi tool."""
    def query(self, user_input: str) -> Dict[str, Any]:
        return {"answer": f"[Chatbot Baseline] Trả lời cho: {user_input}",
                "tool_calls": [], "status": "success", "mode": "mock_baseline"}

class ToolCallingAgent:
    """Agent giả lập có nhận diện intent, gọi tool, trace và giới hạn bước."""
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.trace: List[Dict[str, Any]] = []

    def _detect_intents(self, user_input: str) -> Dict[str, Any]:
        lower = user_input.lower()
        faq = any(k in lower for k in ("chính sách", "bảo hành", "đổi trả", "bao lâu"))
        catalog_action = any(k in lower for k in ("xem", "tìm", "mua", "giá dưới", "dưới", "gợi ý"))
        ticket = any(k in lower for k in ("bị lỗi", "bị hỏng", "ẩm mốc", "khiếu nại",
                    "phản hồi", "phản ánh", "ghi nhận", "sự cố", "cần xử lý", "ticket"))
        category = ("du_lich" if any(k in lower for k in ("resort", "vinpearl", "du lịch", "nghỉ dưỡng"))
                    else "xe_dien" if any(k in lower for k in ("xe điện", "vinfast", "xe vf", "ô tô"))
                    else None)
        needs_catalog = bool(category and catalog_action and not (faq and not ticket))
        if ticket and not any(k in lower for k in ("xem", "tìm", "mua", "giá dưới", "cho tôi xem")):
            needs_catalog = False
        catalog_args = {"category": category} if needs_catalog else {}
        price = re.search(r"(?:dưới|không quá|tối đa)\s*(\d+(?:[.,]\d+)?)\s*(triệu|tr|tỷ)", lower)
        if price and needs_catalog:
            catalog_args["max_price"] = int(float(price.group(1).replace(",", ".")) *
                                            (1_000_000_000 if price.group(2) == "tỷ" else 1_000_000))
        ticket_args = {}
        if ticket:
            name = re.search(r"(?:tôi\s+tên|tên\s+tôi\s+là|tên\s+là|tôi\s+là)\s+([^,.]+?)(?=,|\.|\s+(?:xe|phòng|tôi|bị|và)\b|$)",
                             user_input, flags=re.IGNORECASE)
            issue = re.search(r"(?:xe|phòng|sản phẩm|dịch vụ)[^,.]*?(?:bị|lỗi|hỏng)[^,.]*",
                              user_input, flags=re.IGNORECASE)
            ticket_args = {"customer_name": name.group(1).strip() if name else "Khách hàng chưa cung cấp tên",
                           "issue_description": issue.group(0).strip() if issue else user_input.strip(),
                           "priority": "high" if any(k in lower for k in ("nghiêm trọng", "khẩn cấp", "gấp"))
                                       else "low" if "không gấp" in lower else "medium"}
        return {"needs_catalog": needs_catalog, "needs_ticket": ticket,
                "is_faq": faq and not needs_catalog and not ticket,
                "catalog_args": catalog_args, "ticket_args": ticket_args}

    def run(self, user_input: str) -> Dict[str, Any]:
        self.trace = []
        intents = self._detect_intents(user_input)
        actions = []
        if intents["needs_catalog"]:
            actions.append(("search_product_catalog", intents["catalog_args"]))
        if intents["needs_ticket"]:
            actions.append(("submit_support_ticket", intents["ticket_args"]))
        if not actions:
            answer = ("Về chính sách bảo hành, vui lòng tham khảo điều kiện bảo hành "
                      "chính thức của VinFast cho dòng xe cụ thể." if intents["is_faq"] else
                      "Tôi hỗ trợ tra cứu sản phẩm VinFast/Vinpearl và tiếp nhận phản hồi.")
            self.trace.append({"step": 1, "action": "respond", "answer": answer})
            return {"answer": answer, "trace": self.trace, "iterations": 1, "status": "completed"}
        if self.max_iterations < len(actions):
            return {"answer": "Đã đạt giới hạn số bước xử lý.", "trace": self.trace,
                    "iterations": max(0, self.max_iterations), "status": "max_iterations_reached"}
        responses = []
        for iteration, (name, args) in enumerate(actions, 1):
            observation = TOOL_MAP[name](**args)
            self.trace.append({"step": iteration, "action": name, "args": args,
                               "observation": observation})
            if name == "search_product_catalog":
                if observation and "error" not in observation[0]:
                    responses.append("Sản phẩm phù hợp:\n" + "\n".join(
                        f"{p['name']}: {p['price_vnd']:,} VNĐ" for p in observation))
                else:
                    responses.append("Rất tiếc, không tìm thấy sản phẩm phù hợp.")
            else:
                responses.append(f"Đã tạo phiếu {observation['ticket_id']} cho "
                                 f"{observation['customer_name']} (ưu tiên: {observation['priority']}).")
        return {"answer": "\n".join(responses), "trace": self.trace,
                "iterations": len(actions), "status": "completed"}

def main():
    query = "Tôi muốn xem xe điện VinFast giá dưới 600 triệu."
    print("=== RUNNING CHATBOT BASELINE ===")
    print(ChatbotBaseline().query(query))
    print("\n=== RUNNING TOOL CALLING AGENT ===")
    agent = ToolCallingAgent(max_iterations=5)
    result = agent.run(query)
    print("Result:", result["answer"])
    print("Trace Log:", json.dumps(agent.trace, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
