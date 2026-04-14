# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Thành Đại Khánh
**Vai trò trong nhóm:** Supervisor Owner / Tech Lead
**Ngày nộp:** 14/04/2026


---

## 1. Tôi phụ trách phần nào? (150 từ)

Trong bài thực hành Lab Day 09, tôi đảm nhận vai trò **Tech Lead** và là người trực tiếp code file `graph.py` (**Supervisor Owner**). Trách nhiệm chính của tôi là thiết lập luồng kết nối các Agent theo cấu trúc dự án.

**Module/file tôi chịu trách nhiệm:**
- **`graph.py`**: Tôi đã xây dựng logic điều hướng (`supervisor_node`) và quản lý State chung (`AgentState`). Tôi setup luồng Supervisor-Worker để các Agent chạy theo đúng thứ tự bài lab yêu cầu.
- **`contracts/worker_contracts.yaml`**: Tôi đã tạo file này để thống nhất cấu trúc Input/Output giữa các Worker (do Minh viết) và MCP (do Thành viết), giúp quá trình ghép code ít bị lỗi key.
- **Environment & Git**: Tôi tạo `.gitignore` để loại bỏ `.env` và thư mục `chroma_db` khỏi repo, tránh bị conflict khi các thành viên pull code.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Code trong `graph.py` đóng vai trò là hàm main của Pipeline. Kết quả từ `retrieval` hoặc `policy` worker sẽ được lưu vào `AgentState`, sau đó `graph.py` chuyển State này tới `synthesis_worker` để sinh câu trả lời cuối cùng. 

**Bằng chứng:**
- File: `day09/lab/graph.py` (Functions: `supervisor_node`, `run_graph`).
- File: `day09/lab/contracts/worker_contracts.yaml`.
- Lịch sử Git: Commit file bộ khung ban đầu và merge code.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (200 từ)

**Quyết định:** Tôi quyết định dùng **Keyword Matching** (Rule-based) với list các từ khóa cụ thể để làm logic định tuyến (Routing) trong `supervisor_node` thay vì gọi mô hình LLM để phân loại (LLM Classifier).

**Các lựa chọn thay thế:**
- Tạo một prompt gửi vào gpt-4o-mini để yêu cầu model output ra luồng cần đi ("retrieval" hoặc "policy").

**Tại sao tôi chọn cách này?**
1. **Tiết kiệm thời gian (Latency):** Việc gọi thêm LLM chỉ để phân tích ý định sẽ làm mất thêm khoảng 1-2 giây. Quy tắc dựa trên if-else từ khóa chạy gần như tức thời.
2. **Dễ debug:** Với cấu trúc if-else, tôi dễ dàng in ra chính xác từ khóa nào đã khiến Supervisor rẽ nhánh. Báo cáo trace sẽ rõ ràng hơn.

**Trade-off đã chấp nhận:**
Sử dụng keyword matching sẽ thất bại nếu user không dùng đúng từ vựng trong danh sách (vd: không nói "hoàn tiền" mà nói "trả lại tiền"). Tôi bù đắp phần này bằng cách cấu hình nhánh `retrieval_worker` làm nhánh fallback mặc định.

**Bằng chứng từ trace/code:**
```python
# Trích đoạn code trong graph.py
found_policy = [kw for kw in policy_keywords if kw in task]
if found_policy:
    route = "policy_tool_worker"
    route_reason = f"task contains policy keywords: {found_policy}"
```
Trace mẫu (ví dụ với file thực tế `run_20260414_150330.json`): `"route_reason": "task contains policy keywords: ['cấp quyền', 'access', 'level 3']"`.

---

## 3. Tôi đã sửa một lỗi gì? (200 từ)

**Lỗi:** Mất kết nối DB do sai lệch đường dẫn tương đối (Path Resolution Issue).

**Symptom:**
Lúc đầu, khi chạy `python graph.py`, Worker truy xuất ChromaDB bị lỗi `FileNotFoundError` hoặc không tìm thấy dữ liệu.

**Root cause:**
Lỗi do dùng đường dẫn tương đối để trỏ về ChromaDB của bài Day 08. Khi script chạy ở các thư mục hiện hành (CWD) khác nhau (như chạy qua `eval_trace` thay vì chạy trực tiếp file worker), đường dẫn tương đối `../day08/lab/chroma_db` trỏ sai vị trí.

**Cách sửa:**
Tôi đã cập nhật file `workers/retrieval.py` để sử dụng đường dẫn tuyệt đối (Absolute Path). Thay vì dùng chuỗi tương đối, tôi kết hợp `os.path.dirname(__file__)` để lúc nào hàm cũng trỏ chính xác về thư mục CSDL bất kể file nào đang gọi hàm thư viện đó.

**Bằng chứng trước/sau:**
- **Trước khi sửa:** Log: `ERROR: Path does not exist: ../day08/lab/chroma_db` -> Answer: "Tôi xin lỗi...".
- **Sau khi sửa:**
```bash
DEBUG: Connecting to ChromaDB at: C:\Users\WBPC.VN\Documents\GitHub\Lecture-Day-08-09-10-new\day08\lab\chroma_db
✓ route=retrieval_worker, conf=0.90, 6243ms
```

---

## 4. Tôi tự đánh giá đóng góp của mình (150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tổ chức file `worker_contracts.yaml` giúp các bạn trong nhóm thống nhất được tên biến của `AgentState` từ rất sớm, nhờ đó khi copy code của từng người lại với nhau ít bị lỗi key báo thiếu.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Ở cờ HITL (Human-In-The-Loop) khi bắt nguy cơ cao từ lỗi lạ kiểu `ERR-403`, hiện Supervisor mới chỉ in ra dòng cảnh báo thay vì thực sự cấu hình state để tạm ngưng quy trình.

**Nhóm phụ thuộc vào tôi ở đâu?**
Các Worker sẽ không biết khi nào cần chạy nếu `graph.py` của tôi trả về sai `supervisor_route`. Code phần khung State là bắt buộc phải xong thì Minh và Thành mới có cái để chạy chung.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi cần thư viện Retrieval truy xuất chính xác từ Minh để pipeline trả kết quả tốt. Khâu đánh giá trace từ script Eval của Thành cũng giúp tôi nhận ra Supervisor bắt keyword đúng/sai chỗ nào để tự review.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (100 từ)

Tôi sẽ sử dụng prompt LLM nhẹ (ví dụ model `gpt-4o-mini` với max_tokens = 5) làm nhiệm vụ Supervisor Classifier để thay cho việc if-else rule-based. Rule-based như hiện tại dù nhanh nhưng sẽ trật khi người dùng dùng từ đồng nghĩa. Qua trace đối với câu lỗi lạ `ERR-403` (câu số 9), bộ quy tắc hiện nay chỉ bắt được khi có chữ chính xác, việc chuyển sang LLM phân tích sẽ tốn thêm cost tính toán nhưng làm giảm rủi ro routing sai lệch trong thực tế ảo.

---
