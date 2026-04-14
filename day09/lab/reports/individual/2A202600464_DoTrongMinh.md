# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Đỗ Trọng Minh  
**Vai trò trong nhóm:** Supervisor Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** ~700 từ

---

## 1. Tôi phụ trách phần nào? (150 từ)

Trong buổi Lab hôm nay, tôi chịu trách nhiệm chính về "bộ não" điều phối của toàn bộ hệ thống trợ lý trợ giúp nội bộ. Công việc của tôi tập trung vào việc chuyển đổi pipeline RAG đơn khối (monolith) từ Day 08 sang kiến trúc **Supervisor-Worker** linh hoạt hơn.

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py`
- Functions tôi implement: `supervisor_node()` (phân tích intent), `route_decision()` (điều hướng logic), và `make_initial_state()` (quản lý trạng thái AgentState).

Tôi đóng vai trò trung tâm kết nối các thành viên: tôi nhận contract đầu ra từ **Retrieval Owner** và **Policy Owner** để định nghĩa luồng dữ liệu trong `AgentState`. Đồng thời, tôi phối hợp với **MCP Owner** để tích hợp các tín hiệu `needs_tool` vào logic quyết định của Supervisor, giúp hệ thống biết khi nào cần gọi external capabilities thay vì chỉ tra cứu tài liệu tĩnh.

**Bằng chứng:** Code trong file `graph.py` với logic routing dựa trên keyword và risk detection tại các dòng từ 84 đến 139.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (200 từ)

**Quyết định:** Tôi chọn triển khai **Rule-based Routing kết hợp Risk Detection** trong `supervisor_node` thay vì sử dụng hoàn toàn LLM để phân loại (LLM Classifier).

**Lý do:**
1. **Hiệu năng (Latency):** Qua thực tế chạy `eval_trace.py`, mỗi lần gọi LLM tốn từ 800ms - 1.5s. Bằng cách dùng keyword mapping cho các intent rõ ràng (như "refund", "access", "SLA"), tôi giảm thời gian routing xuống dưới 10ms.
2. **Độ tin cậy:** Với các yêu cầu nhạy cảm như "cấp quyền" (access control) hay "sự cố P1", việc tin tưởng hoàn toàn vào LLM có thể dẫn đến sai sót routing. Tôi áp dụng thêm một lớp `risk_keywords` để tự động bật flag `risk_high`, bắt buộc hệ thống phải đi qua `policy_tool_worker` hoặc chuẩn bị cho `human_review`.

**Trade-off:** Cách làm này đòi hỏi tôi phải bảo trì danh sách keyword thủ công. Tuy nhiên, trong phạm vi 5 nhóm tài liệu của Lab, đây là lựa chọn tối ưu giữa tốc độ và sự kiểm soát.

**Bằng chứng từ trace:** Trong file `run_20260414_150344.json`, câu hỏi về "Ticket P1 lúc 2am" đã được Supervisor nhận diện đúng:
```json
"route_reason": "task contains policy keywords: ['access'] | risk detected: ['emergency', '2am']",
"risk_high": true,
"supervisor_route": "policy_tool_worker"
```
Kết quả là hệ thống đã kích hoạt đúng Worker xử lý chính sách khẩn cấp thay vì chỉ retrieve thông tin thông thường.

---

## 3. Tôi đã sửa một lỗi gì? (200 từ)

**Lỗi:** Inconsistent Path Configuration & FileNotFoundError during Trace Evaluation.

**Symptom:** Khi chạy script đánh giá `eval_trace.py` từ thư mục gốc của repo, hệ thống báo lỗi `FileNotFoundError: [Errno 2] No such file or directory: 'data/test_questions.json'`. Đồng thời, Retrieval Worker không tìm thấy database ChromaDB do đường dẫn tương đối bị sai lệch giữa các cấp thư mục.

**Root cause:** Logic khai báo đường dẫn trong `retrieval.py` (`CHROMA_DB_PATH`) mặc định tìm về `day08/lab`, nhưng cấu trúc thư mục thực tế sau khi `git pull` đã thay đổi, khiến script chạy từ thư mục cha không định vị được folder `data/` và `chroma_db/`.

**Cách sửa:**
1. Tôi đã điều chỉnh lại `CWD` khi thực thi bằng cách di chuyển hẳn vào thư mục `/day09/lab/`.
2. Tôi cập nhật lại biến `CHROMA_DB_PATH` trong `workers/retrieval.py` sử dụng `os.path.abspath` và `__file__` để đảm bảo đường dẫn luôn đúng bất kể script được gọi từ đâu.
3. Cấu hình lại file `.env` để đảm bảo API Key được nạp đúng sau khi merge code từ các thành viên khác.

**Bằng chứng:** Terminal log đã chuyển từ lỗi Exit Code 1 sang trạng thái chạy thành công 15/15 test questions:
`📋 Running 15 test questions from data/test_questions.json...`

---

## 4. Tôi tự đánh giá đóng góp của mình (100 từ)

**Tôi làm tốt nhất ở điểm nào?**  
Khả năng debug hệ thống (Trace tracking). Tôi đã thiết lập format trace JSON rất chi tiết, giúp nhóm dễ dàng nhận ra bước nào trong graph bị fail (ví dụ: phát hiện `policy_result` trả về `unknown` do thiếu context).

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**  
Logic xử lý `human_review_node` hiện tại vẫn chỉ là placeholder tự động approve. Nếu có lỗi nghiêm trọng, hệ thống vẫn sẽ thực hiện tiếp thay vì dừng lại chờ người dùng thật.

**Nhóm phụ thuộc vào tôi ở đâu?**  
Tôi là người xây dựng `AgentState`. Nếu tôi thay đổi cấu trúc dữ liệu trong state mà không báo trước, tất cả các Workers của các bạn khác sẽ bị crash do không tìm thấy key cần thiết.

**Phần tôi phụ thuộc vào thành viên khác:**  
Tôi phụ thuộc hoàn toàn vào output của **Worker Owners**. Nếu `policy_tool.py` trả về kết quả không đúng format contract đã thỏa thuận, Supervisor của tôi sẽ không thể chuyển dữ liệu sang `synthesis_block`.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50 từ)

Tôi sẽ nâng cấp Supervisor lên thành **Dynamic Router** sử dụng LangGraph `interrupt_before`. Dựa trên trace của các câu hỏi phức tạp (như mã lỗi `ERR-403`), tôi thấy hệ thống cần một bước "dừng khẩn cấp" thực sự để nhân viên IT can thiệp vào state trước khi trả lời khách hàng.
