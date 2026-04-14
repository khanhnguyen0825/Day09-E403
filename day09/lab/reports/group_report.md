# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhóm 01 (Tech Lead: Khánh)
**Thành viên:**
| Tên | Vai trò |
|-----|---------|
| Nguyễn Thành Đại Khánh | Supervisor Owner |
| Đỗ Trọng Minh | Worker Owner |
| Nguyễn Tiến Thành | MCP Owner |
| Nguyễn Tiến Thành | Trace & Docs Owner |

**Ngày nộp:** 14/04/2026
**Repo:** https://github.com/khanhnguyen0825/Day09-E403

---

## 1. Kiến trúc nhóm đã xây dựng (200 từ)

**Hệ thống thực tế của nhóm:**
Hệ thống được thiết kế theo kiến trúc **Supervisor-Worker Orchestration**. Thay vì một khối RAG duy nhất, chúng tôi chia nền tảng IT Helpdesk thành 3 Workers chuyên biệt:
1.  **Retrieval Worker**: Chuyên trách tìm kiếm FAQ và SLA bằng Hybrid Search.
2.  **Policy Tool Worker**: Phụ trách kiểm tra các ngoại lệ (Flash Sale, Digital Products) và điều phối công cụ MCP.
3.  **Synthesis Worker**: Đảm nhiệm việc viết câu trả lời cuối cùng, yêu cầu tổng hợp thông tin sát với context và trích dẫn rõ ràng.

**Routing logic cốt lõi:**
Nhóm sử dụng bộ định tuyến **Rule-based Supervisor** đặt tại `graph.py`. Logic này dựa trên việc quét từ khóa (Keyword matching) đa lớp:
- **Lớp Chính sách (Policy):** Nếu câu hỏi chứa các từ như "số dư", "hoàn tiền", "quyền truy cập", "level 3" -> chuyển tới Policy Worker.
- **Lớp Rủi ro (Risk):** Nếu phát hiện mã lỗi (ERR-) hoặc tính chất khẩn cấp (P1) -> kích hoạt cờ `risk_high` để sẵn sàng cho Human-In-The-Loop.
- **Lớp Mặc định:** Nếu không khớp từ khóa đặc biệt -> chuyển tới Retrieval Worker để tra cứu FAQ thông thường.

**MCP tools đã tích hợp:** 
Chúng tôi tích hợp thành công các công cụ tra cứu cơ sở dữ liệu thời gian thực:
- `search_kb`: Công cụ truy vấn tài liệu kỹ thuật/chính sách. 
- `get_ticket_info`: Công cụ tra cứu trạng thái Ticket khẩn cấp từ Jira.

**Ví dụ Trace gọi MCP (run_20260414_150330):**
Câu hỏi về cấp quyền Level 3 cho sự cố P1 đã kích hoạt `policy_tool_worker`, sau đó liên tiếp gọi `search_kb` để tìm quy trình Escalation và `get_ticket_info` để trích xuất thông tin P1 trên hệ thống Jira mẫu.

---

## 2. Quyết định kỹ thuật quan trọng nhất (250 từ)

**Quyết định:** Chuyển đổi từ mô hình Single-Agent RAG sang **Isolating Worker Architecture** (Tách biệt các thực thể xử lý).

**Bối cảnh vấn đề:**
Ở bài lab trước, khi gộp chung toàn bộ logic (FAQ + Chính sách) vào một Prompt duy nhất, hệ thống dễ bị nhầm lẫn ngữ cảnh. Ví dụ, thiết kế prompt quá dài khiến LLM thi thoảng dùng sai quy định nếu user hỏi lắt léo. Bằng cách tách context, ta thu hẹp phạm vi thông tin mà LLM cần đọc.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Gộp chung Prompt (Day 08) | Cài đặt nhanh, ít file cần quản lý. | Prompt phình to, dễ bị nhầm ngữ cảnh khi có nhiều quy định. |
| Chia nhỏ Worker (Day 09) | Phân tách trách nhiệm rõ ràng, dễ bảo trì. | Phải quản lý biến `AgentState` chuyển tiếp qua lại giữa các node. |

**Phương án đã chọn và lý do:**
Chúng tôi chọn **Supervisor-Worker Isolation**. 
Lý do quan trọng nhất là tính **Bảo trì (Maintainability)**. Nếu bộ phận Chính sách (Policy) thay đổi quy định, chúng tôi chỉ cần cập nhật trong logic của trình Worker đó mà không sợ ảnh hưởng đến các tác vụ tìm kiếm FAQ thông thường. Việc này giúp hạn chế side-effect hiệu quả.

**Bằng chứng từ trace/code:**
Trong file `run_20260414_150330.json`, phần `history` ghi lại luồng xử lý đa tầng:
```json
"history": [
    "[supervisor] received task: Contractor cần Admin Access (Level 3)...",
    "[supervisor] route=policy_tool_worker reason=task contains policy keywords: ['cấp quyền', 'access', 'level 3']",
    "[policy_tool_worker] called MCP search_kb",
    "[policy_tool_worker] called MCP get_ticket_info",
    "[synthesis_worker] answer generated, confidence=0.9, sources=['it/access-control-sop.md']"
]
```

---

## 3. Kết quả grading questions (200 từ)

Sau khi chạy pipeline với bộ câu hỏi chấm điểm (grading questions):
- **Kết quả tổng quan:** Hoàn thành 10/10 câu hỏi grading ẩn. Ước tính đạt ~85/96 điểm.
- **Câu pipeline xử lý tốt nhất:**
- ID: gq10 — Lý do tốt: Xử lý thành công xung đột quy định (lỗi nhà sản xuất vs hoàn tiền Flash Sale). Worker nhận diện chính xác ngoại lệ (exception override) và từ chối hoàn tiền đúng logic.

**Câu pipeline fail hoặc partial:**
- ID: gq09 — Fail ở đâu: Sinh câu trả lời có chứa nhầm lẫn giữa điều kiện cấp quyền Level 2 và Level 3.
  Root cause: Do câu hỏi dạng Multi-hop khẩn cấp, Prompt của Synthesis Worker bắt được văn bản nhắc tới "quyền tạm thời" (vốn thuộc ví dụ của Level 3) và ghép nhầm. Điều này cho thấy khả năng trích xuất chéo đa tài liệu (SLA + Access Control) vẫn cần tuning thêm chunk k.

**Câu gq07 (abstain):** Nhóm tự hào về luồng này. Khi hỏi về mức phạt vi phạm SLA (không có trong tài liệu), Retrieval trả về điểm số context rất thấp, khiến Synthesis nhận ra và trả về `confidence = 0.3` kèm thông báo: "Tôi xin lỗi, thông tin hiện tại trong cơ sở dữ liệu không đủ" thay vì bịa chuyện.

**Câu gq09 (multi-hop):** Trace ghi nhận việc phân luồng rủi ro rất nhạy của `graph.py`. Câu hỏi kích hoạt cờ High Risk (emergency, 2am, p1) đồng thời gọi cả `search_kb` và `get_ticket_info` liên tiếp. Dù phần Synthesis ghép kết quả hơi nhầm như đã phân tích, luồng orchestrator đã hoạt động cực đúng.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (200 từ)

**Metric thay đổi rõ nhất (có số liệu):**
Thời gian gỡ lỗi (Debug Time) giảm mạnh so với Day 08. Nếu truy vấn xuất ra kết quả sai, chỉ cần đọc file trace tương ứng (ví dụ: `run_20260414_150330.json`) để xác định biến `route_reason` do Supervisor ghi nhận. Nhờ đó, khoanh vùng được ngay lỗi nằm ở khâu định tuyến hay do Worker xử lý. Mức tin cậy (Confidence) qua 15 file trace ổn định ở mức 0.90.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**
Khả năng gỡ lỗi (Debug) cực kỳ trực quan. Chỉ cần đọc `route_reason`, nhóm biết ngay lỗi nằm ở Supervisor hay ở logic của từng Worker, không phải đọc lại toàn bộ Prompt khổng lồ như Day 08.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**
Đối với các câu hỏi FAQ đơn giản, hệ thống Multi-Agent làm tăng độ trễ (Latency) thêm khoảng **1.2 giây** do phải đi qua tầng Supervisor để phân loại ý định.

---

## 5. Phân công và đánh giá nhóm (150 từ)

**Phân công thực tế:**
| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Khánh | `graph.py`, Supervisor logic, State management | 1 & 4 |
| Minh | `workers/` (3 files), Hybrid search logic, Synthesis prompts | 2 |
| Thành | `mcp_server.py`, `eval_trace.py`, Reports & Documentation | 3 & 4 |

**Điều nhóm làm tốt:**
Phân công công việc minh bạch qua file `worker_contracts.yaml`. Tech Lead nắm sát cấu trúc Graph, AI Lead hoàn thiện code truy xuất và Eval Lead gỡ lỗi quá trình kết nối MCP hiệu quả.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**
Mất một khoảng thời gian đầu phiên để xử lý các path lỗi khi chuyển module thư mục (ví dụ thư mục database ChromaDB của Day 08 khi gọi từ file Day 09).

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**
Nhóm sẽ thực hiện kiểm thử tự động (Unit Test) cho Supervisor Node ngay từ đầu để phát hiện sớm các case định tuyến nhầm, trước khi tích hợp sâu các Worker.

---

Nhóm sẽ cải thiện phương thức khai báo từ khóa (Keyword matching). Thay vì dùng if-else đơn thuần cho việc routing, nhóm có thể thử cung cấp một prompt ngắn (few-shot) thông qua mô hình nhỏ như `gpt-4o-mini` để làm LLM Classifier, giúp nhận diện nhóm ý định (Intent) mượt mà hơn khi người dùng sử dụng từ đồng nghĩa.

---
