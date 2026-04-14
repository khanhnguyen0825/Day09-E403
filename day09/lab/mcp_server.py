"""
mcp_server.py — Mock MCP Server
Sprint 3: Cung cấp các công cụ (tools) cho Agent thông qua giao thức MCP.
"""

import os
from typing import Dict, Any, List

# --- MOCK DATA cho Ticket (Giả lập database Jira/ITSM) ---
MOCK_TICKETS = {
    "P1-LATEST": {
        "id": "P1-2026-001",
        "title": "Hệ thống thanh toán lỗi diện rộng",
        "status": "In Progress",
        "priority": "P1 - Critical",
        "assignee": "Senior Engineer A",
        "created_at": "2026-04-13T02:00:00",
    },
    "TICKET-403": {
        "id": "IT-403",
        "title": "Yêu cầu cấp quyền cập nhật lỗi ERR-403",
        "status": "Pending Approval",
        "priority": "P2 - High",
        "assignee": "IT Helpdesk B",
        "created_at": "2026-04-13T10:00:00",
    }
}

def search_kb(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Công cụ tìm kiếm trong Knowledge Base (Dùng retrieval worker)."""
    from workers.retrieval import retrieve_hybrid
    try:
        chunks = retrieve_hybrid(query, top_k=top_k)
        return {
            "chunks": chunks,
            "status": "success",
            "count": len(chunks)
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def get_ticket_info(ticket_id: str) -> Dict[str, Any]:
    """Công cụ tra cứu thông tin ticket Jira."""
    ticket = MOCK_TICKETS.get(ticket_id.upper())
    if not ticket:
        return {
            "status": "not_found", 
            "error": f"Ticket {ticket_id} không tồn tại trên hệ thống Jira."
        }
    return {
        "ticket": ticket,
        "status": "found",
        "source": "Jira Service Management"
    }

def dispatch_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hàm điều phối (Router cho MCP tools).
    Trong thực tế, đây là nơi MCP Server nhận request từ Client.
    """
    if tool_name == "search_kb":
        return search_kb(tool_input.get("query", ""), tool_input.get("top_k", 3))
    elif tool_name == "get_ticket_info":
        return get_ticket_info(tool_input.get("ticket_id", ""))
    else:
        raise ValueError(f"Tool {tool_name} không tồn tại trên hệ thống MCP.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    import sys
    load_dotenv()
    
    # Fix UTF-8 display on Windows
    # sys.stdout.reconfigure(encoding='utf-8') is not needed for IDEs usually but safe for terminal
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    # Test nhanh MCP tools
    print("Testing search_kb tool:")
    print(search_kb("SLA P1 là bao lâu?"))
    
    print("\nTesting get_ticket_info tool:")
    print(get_ticket_info("P1-LATEST"))
    
    print("\nTesting missing ticket:")
    print(get_ticket_info("TICKET-999"))
