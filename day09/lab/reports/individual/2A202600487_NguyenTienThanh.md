# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Tiến Thành  
**Vai trò trong nhóm:** MCP Owner / Trace & Docs Owner (Eval Lead)  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** Khoảng 600 từ

---

## 1. Tôi phụ trách phần nào?

**Module/file tôi chịu trách nhiệm:**
- Xây dựng và quản lý Tool API: `mcp_server.py` (Sprint 3)
- Quản lý kịch bản đo kiểm: `eval_trace.py` (Sprint 4)
- Thiết kế tài liệu Document & Architecture: `docs/*` (Sprint 4)

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Công việc của tôi đóng vai trò mũi nhọn "Tiền tuyến" và "Hậu phương" của toàn dự án. Ở tiền tuyến, tôi viết `mcp_server.py` — cung cấp hệ thống API Mock (Giả lập Ticket, KB Search) để Worker Agent do bạn Minh thiết kế có thể Query vào, lấy data thực tiễn giải quyết bài toán cấp quyền Khẩn cấp P1. Ở hậu phương, script `eval_trace.py` của tôi bọc quanh Graph Pipeline của bạn Khánh, vận hành nó chạy vòng lặp 15 lần để in ra bộ Trace (.json) hoàn chỉnh nhất, làm dữ liệu thô phục vụ phân tích so sánh Day 08 và Day 09.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
Các commit đẩy lên nhánh `main` 14/04: 
- feat(sprint-3): enhance MCP server with graceful ticket fallback and standalone mode
- fix(sprint-4): resolve UTF-8 encoding issues in eval script and setup baselines
- chore(sprint-4): generate 15 routing traces and metrics comparison report
- docs(sprint-4): complete system architecture, routing decisions, and single vs multi comparisons

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** Implementing Graceful Fail (Lỗi có kiểm soát) thay vì Hardcoded Mock Data mặc định cho Tool dò Ticket.

**Lý do:**
Chức năng `get_ticket_info(ticket_id)` trong `mcp_server.py` ban đầu được thiết kế thô bằng cách "Nếu người gọi nhập sai ID, cứ trả về Ticket P1 làm mặc định". Tôi quyết định bác bỏ logic này. Bởi kiến trúc Multi-Agent của lab yêu cầu bảo mật, nếu trả về Ticket mồi P1 mọi nơi, Policy Worker của Minh sẽ có nguy cơ bị "ảo giác" (Hallucinate) - nghĩ rằng thực sự có một vé P1 đang mở để xét duyệt cấp quyền sai quy định.
Chính vì vậy, tôi chuyển sang cách trả về `{"status": "not_found", "error": "Ticket X không tồn tại"}`. Khi Agent nhận được báo cáo này, nó sẽ bị từ chối Tool Calls, buộc Synthesis Worker phải "Abstain" (xin lỗi, tôi không thể tìm thấy).

**Trade-off đã chấp nhận:**
Có thể khiến câu trả lời của Bot trở nên cụt ngủn ("Xin lỗi") thay vì lúc nào cũng trả về một mẫu câu dài dòng nhưng bịa đặt. Cost đánh đổi là UX bị khô khan, nhưng Integrity (Tính toàn vẹn Dữ liệu) được bảo toàn.

**Bằng chứng từ trace/code:**
Code tôi đã sửa tại `mcp_server.py`:
```python
ticket = MOCK_TICKETS.get(ticket_id.upper())
if not ticket:
    return {
        "status": "not_found", 
        "error": f"Ticket {ticket_id} không tồn tại trên hệ thống Jira."
    }
```

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** Ngừng Crash đột ngột do `UnicodeEncodeError` khi Agent sinh ra đáp án Tiếng Việt.

**Symptom (pipeline làm gì sai?):**
Lúc tôi chạy file `python mcp_server.py` để test độc lập luồng lấy đồ thị, khi in danh sách Dictionary chứa chuỗi có dấu (Ví dụ: "Hệ thống thanh toán lỗi diện rộng"), Powershell mặc định trên Windows (sử dụng CodePage 1252) bị sập ngay lập tức. Sau đó khi chạy tới file khảo sát `eval_trace.py` thì lại bị `UnicodeDecodeError` khi Load JSON đứt đoạn. Vấn đề này chặn đứng toàn bộ Workflow tạo File Log jsonl.

**Root cause (lỗi nằm ở đâu):**
Lỗi nằm ở Stdout của môi trường Windows chưa config UTF-8 và hàm `json.load()` mặc định của Python đọc file JSON theo định dạng ANSI/cp1252 khi chạy nội bộ.

**Cách sửa:**
Tôi thêm thư viện OS và ép Terminal của Powershell tự định dạng lại encoding chuẩn nhất theo chuẩn quốc tế ngay từ đoạn Boot ban đầu, đồng thời rào thêm từ khoá encoding vào hàm I/O.

**Bằng chứng trước/sau:**
Trước khi sửa (Lỗi System out):
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u1ec7' in position 44
```

Sau khi tôi rào cục Code sau đây trong luồng `__main__`, mọi Test Questions chạy mượt 100%:
```python
try:
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass
with open(os.path.join(traces_dir, fname), encoding="utf-8") as f:
```

---

## 4. Tôi tự đánh giá đóng góp của mình

**Tôi làm tốt nhất ở điểm nào?**
Khả năng dò Bug và kiểm thử tính toàn vẹn của một API Server cục bộ (Isolation Testing). Tôi test Server MCP đứng độc lập trước khi ráp nó cho cả nhóm, nhờ đó cứu cả nhóm khỏi quả lỗi Unicode Crash sập rạp. Đồng thời xử lý số liệu Trace thô thành Documentation báo cáo rất rành mạch.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Ban đầu tôi định dựng `mcp_server.py` thành một Restful API (FastAPI) thực thụ theo mức Advanced Requirement (+Bonus Mức điểm), nhưng vì có rào cản thời gian và đồng bộ mạng LAN cho các máy của nhóm nên đành hạ chuẩn xuống chạy qua thư viện Component ảo (Mock/Func calling).

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu tôi giải quyết Tool API MCP chậm, bạn Minh sẽ không thể lập trình được luồng Logic cấm / duyệt cho "Flash Sale" hay cho thẻ "P1-Level 3" (Vì Agent không móc được dữ liệu thật). Và nếu file `eval_trace` của tôi bị lỗi, nhóm không thể có số đo độ trễ Latency để chứng minh Day 09 xịn hơn Day 08.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi không thể phân tích độ chính xác luồng Routing Distribution (Luồng rẽ) nếu file `graph.py` của Khánh chưa hoàn thiện biến State Object.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi sẽ xây dựng **hệ thống Server HTTP Fast-API** chuẩn hoá Protocol MCP thực thụ tách rời khỏi Codebase, sau đó cấp quyền Endpoint cho Graph truy xuất Proxy. Điều này có thể giải phóng bộ nhớ RAM cục bộ trong kịch bản Eval (Chạy đồng loạt 15 câu thì System sẽ nhẹ RAM hơn do luồng Worker API chạy External Server riêng).
