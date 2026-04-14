"""
workers/synthesis.py — Synthesis Worker
Sprint 2: Tổng hợp câu trả lời từ retrieved_chunks và policy_result.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: evidence từ retrieval_worker
    - policy_result: kết quả từ policy_tool_worker

Output (vào AgentState):
    - final_answer: câu trả lời cuối với citation
    - sources: danh sách nguồn tài liệu được cite
    - confidence: mức độ tin cậy (0.0 - 1.0)

Gọi độc lập để test:
    python workers/synthesis.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Bạn là chuyên gia hỗ trợ nội bộ (AI Helpdesk) chuyên nghiệp cho khối CS & IT.
Nhiệm vụ của bạn là giải đáp thắc mắc của nhân viên dựa TRỰC TIẾP và CHỈ trên nền tảng dữ liệu (context) được cung cấp.

CÁC QUY TẮC BẮT BUỘC (CRITICAL RULES):
1. TRÍCH DẪN RÕ RÀNG: Luôn gắn [tên_file] ngay sau đoạn thông tin hoặc từng ý.
2. ĐỊNH DẠNG CHUYÊN NGHIỆP: Ưu tiên trả lời bằng bullet points hoặc các đoạn ngắn gọn để dễ đọc.
3. KHÔNG BỊA ĐẶT (ANTI-HALLUCINATION): Nếu câu hỏi vượt ngoài dữ liệu context, từ chối trả lời một cách lịch sự: "Tôi xin lỗi, thông tin hiện tại trong cơ sở dữ liệu không đủ để trả lời câu hỏi này." 
4. THÔNG TIN NHẠY CẢM: Nếu hỏi về thông tin nhạy cảm bảo mật (password, root access), tuyệt đối từ chối và hướng dẫn tạo ticket trên IT-ACCESS.
5. XỬ LÝ CHÍNH SÁCH (POLICY): Nếu có các ngoại lệ (Exception) từ bộ phận chính sách cung cấp, hãy nêu rõ ràng các ngoại lệ đó trước khi kết luận.
"""


def _call_llm(messages: list) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Clean surrogate characters for OpenAI
    for m in messages:
        m["content"] = (
            m["content"].encode("utf-16", "surrogatepass").decode("utf-16", "ignore")
        )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
        max_tokens=600,
    )
    return response.choices[0].message.content


def _build_context(chunks: list, policy_result: dict) -> str:
    parts = []
    if chunks:
        parts.append("--- Hợp đồng & Tài liệu nội bộ ---")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source", "unknown")
            text = chunk.get("text", "")
            parts.append(f"NGUỒN: {source}\nNỘI DUNG: {text}")

    if policy_result and policy_result.get("exceptions_found"):
        parts.append("\n--- Cảnh báo từ bộ phận Chính sách (Policy) ---")
        for ex in policy_result["exceptions_found"]:
            parts.append(f"NGOẠI LỆ: {ex.get('rule', '')}")

    return "\n\n".join(parts) if parts else "Không tìm thấy dữ liệu liên quan."


def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    context = _build_context(chunks, policy_result)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Câu hỏi nhân viên: {task}\n\nDữ liệu tham khảo:\n{context}\n\nCâu trả lời của AI Helpdesk:",
        },
    ]

    answer = _call_llm(messages)
    sources = list({c.get("metadata", {}).get("source", "unknown") for c in chunks})

    # Tính confidence đơn giản
    confidence = 0.9 if chunks else 0.1
    if "xin lỗi" in answer.lower():
        confidence = 0.3

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }


def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "has_policy": bool(policy_result),
        },
        "output": None,
        "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)
        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]

        worker_io["output"] = {
            "answer_length": len(result["answer"]),
            "sources": result["sources"],
            "confidence": result["confidence"],
        }
        state["history"].append(
            f"[{WORKER_NAME}] answer generated, confidence={result['confidence']}, "
            f"sources={result['sources']}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "SYNTHESIS_FAILED", "reason": str(e)}
        state["final_answer"] = f"SYNTHESIS_ERROR: {e}"
        state["confidence"] = 0.0
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Synthesis Worker — Standalone Test")
    print("=" * 50)

    test_state = {
        "task": "SLA ticket P1 là bao lâu?",
        "retrieved_chunks": [
            {
                "text": "Ticket P1: Phản hồi ban đầu 15 phút kể từ khi ticket được tạo. Xử lý và khắc phục 4 giờ. Escalation: tự động escalate lên Senior Engineer nếu không có phản hồi trong 10 phút.",
                "source": "sla_p1_2026.txt",
                "score": 0.92,
            }
        ],
        "policy_result": {},
    }

    result = run(test_state.copy())
    print(f"\nAnswer:\n{result['final_answer']}")
    print(f"\nSources: {result['sources']}")
    print(f"Confidence: {result['confidence']}")

    print("\n--- Test 2: Exception case ---")
    test_state2 = {
        "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì lỗi nhà sản xuất.",
        "retrieved_chunks": [
            {
                "text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền theo Điều 3 chính sách v4.",
                "source": "policy_refund_v4.txt",
                "score": 0.88,
            }
        ],
        "policy_result": {
            "policy_applies": False,
            "exceptions_found": [
                {
                    "type": "flash_sale_exception",
                    "rule": "Flash Sale không được hoàn tiền.",
                }
            ],
        },
    }
    result2 = run(test_state2.copy())
    print(f"\nAnswer:\n{result2['final_answer']}")
    print(f"Confidence: {result2['confidence']}")

    print("\n✅ synthesis_worker test done.")
