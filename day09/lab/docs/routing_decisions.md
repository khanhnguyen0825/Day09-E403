# Routing Decisions Log — Lab Day 09

**Nhóm:** Khánh - Minh - Thành
**Ngày:** 14/04/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
> 
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> "SLA của lỗi diện rộng ưu tiên cao nhất là bao lâu?"

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `task does not match any specific policy keywords -> general retrieval`  
**MCP tools được gọi:** Không có  
**Workers called sequence:** `retrieval_worker`, `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "SLA cho lỗi mức độ P1 là xử lý trong vòng 4 giờ [sla_p1_2026.txt]."
- confidence: 0.95
- Correct routing? Yes

**Nhận xét:** _(Routing này đúng hay sai? Nếu sai, nguyên nhân là gì?)_
Đúng. Câu hỏi chỉ đang truy vấn thông tin văn bản thông thường, không yêu cầu kiểm tra ngoại lệ chính sách cũng không cung cấp Ticket ID nên việc đưa tới Retrieval Worker là tối ưu.

---

## Routing Decision #2

**Task đầu vào:**
> "Khách hàng Flash Sale yêu cầu hoàn tiền do sản phẩm bị lỗi phần cứng trong hôm nay."

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains "hoàn tiền", "flash sale" -> policy check needed`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `policy_tool_worker`, `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "Rất tiếc, đơn hàng Flash Sale không được áp dụng chính sách hoàn tiền theo Điều 3, policy_refund_v4.txt."
- confidence: 0.90
- Correct routing? Yes

**Nhận xét:**
Tuyệt đối chính xác. Bằng cách định tuyến thẳng tới Policy Worker, Agent đã bỏ qua bước tìm kiếm lang man mà gọi trực tiếp tập luật FlashSale Exception giúp ngăn cản yêu cầu hoàn tiền sai luật.

---

## Routing Decision #3

**Task đầu vào:**
> "Contractor cần Admin Access (Level 3) để khắc phục sự cố P1 đang diễn ra."

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains "p1", "access", "cấp quyền" -> requires emergency access policy`  
**MCP tools được gọi:** `get_ticket_info`  
**Workers called sequence:** `policy_tool_worker`, `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "Vì có sự cố P1 (Hệ thống thanh toán lỗi diện rộng), quản trị viên có thể cấp Level 3 Access tạm thời trong 4 tiếng do tính khẩn cấp."
- confidence: 0.88
- Correct routing? Yes

**Nhận xét:**
Router đã nhận diện được keyword "P1" và "access" để bật cờ Cấp quyền Khẩn cấp. Nhờ gọi Policy_Worker -> lấy Tool JIRA -> Confirm được P1 đang có thật nên mạnh dạn phê duyệt. Nếu rẽ nhầm nhánh Retrieval thì sẽ không bao giờ get được Status ticket.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> _________________

**Worker được chọn:** `___________________`  
**Route reason:** `___________________`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

_________________

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 8 | 53% |
| policy_tool_worker | 7 | 46% |
| human_review | 0 | 0% |

### Routing Accuracy

> Trong số 15 câu nhóm đã chạy, bao nhiêu câu supervisor route đúng?

- Câu route đúng: 15 / 15
- Câu route sai (đã sửa bằng cách nào?): 0
- Câu trigger HITL: 1

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?  
> (VD: dùng keyword matching vs LLM classifier, threshold confidence cho HITL, v.v.)

1. Chúng tôi chọn sử dụng Keyword Matching (Quy tắc Rule-based theo RegEx) để định tuyến vì bài toán có tập Domain rất hữu hạn và cần tốc độ nhanh.
2. Tránh việc LLM đóng vai trò quyết định Route vì làm phí Token (LLM Classification) và tăng độ trễ (Latency) không đáng có so với Rule-based.

### Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?  
> Nếu chưa, nhóm sẽ cải tiến format route_reason thế nào?

Hiện tại `route_reason` (ví dụ: `task contains 'Flash Sale'`) đã làm khá tốt chức năng gỡ lỗi của mình. Tuy vậy, trong tương lai chúng tôi sẽ đưa thêm điểm số của keyword (keyword density) vào để biết được từ khoá nào chiếm tỷ trọng cao nhất dẫn đến rẽ nhánh.
