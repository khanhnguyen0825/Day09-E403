# Báo Cáo Tổng Kết Nhóm — Lab Day 08: RAG Pipeline

**Nhóm:** Khánh - Minh - Thành
**Thành viên:** 
1. Nguyễn Thành Đại Khánh (MSSV: 2A202600404)
2. Đỗ Trọng Minh (MSSV: 2A202600464)
3. Nguyễn Tiến Thành (MSSV: 2A202600487)

---

## 1. Mục tiêu bài lab
Nhóm thực hiện xây dựng một công cụ hỗ trợ trả lời câu hỏi nội bộ (Helpdesk) bằng cách dùng dữ liệu từ các file chính sách (SLA, SOP, Policy) có sẵn. Mục tiêu là để AI trả lời đúng, có trích dẫn nguồn và không tự bịa ra thông tin.

## 2. Cách nhóm thực hiện

Nhóm chia việc làm theo 4 phần chính:

*   **Chuẩn bị dữ liệu:** Nhóm tách văn bản theo từng đoạn (chunking) để AI dễ đọc. Dữ liệu được chuyển thành vector bằng mô hình OpenAI và lưu vào database ChromaDB.
*   **Tìm kiếm (Retrieval):** Để tìm được đúng các từ khóa khó (như mã lỗi ERR-403), nhóm kết hợp cả tìm kiếm theo nghĩa (Dense) và tìm kiếm theo từ khóa (BM25). Sau đó dùng thuật toán RRF để trộn kết quả lại với nhau.
*   **Trả lời (Generation):** Dùng prompt hướng dẫn AI chỉ được trả lời dựa trên tài liệu đưa vào. Nếu không tìm thấy thì phải nói là không biết chứ không được đoán mò.
*   **Chấm điểm:** Dùng một script để AI tự chấm điểm các câu trả lời của hệ thống xem có đúng và đủ ý hay không.

## 3. Kết quả đánh giá

Nhóm đã test thử với 12 câu hỏi và so sánh giữa cách làm cũ (chỉ dùng Dense) và cách làm mới (Hybrid).

| Metric | Bản cũ (Dense) | Bản mới (Hybrid) | Nhận xét |
| :--- | :--- | :--- | :--- |
| **Độ trung thực** | 5.00/5 | 5.00/5 | AI không bịa thông tin |
| **Đúng trọng tâm** | 5.00/5 | 5.00/5 | Trả lời đúng ý câu hỏi |
| **Độ đầy đủ** | 4.83/5 | 4.75/5 | Bản mới giảm nhẹ do bị nhiễu từ khóa |

**Nhận xét:** Hệ thống chạy ổn định, biết từ chối khi hỏi những câu không có trong dữ liệu (như câu hỏi về tiền ăn hay tham nhũng).

## 4. Phân công công việc

*   **Khánh:** Làm phần chuẩn bị dữ liệu, metadata và viết code cho phần tìm kiếm Hybrid ở Sprint 3.
*   **Minh:** Viết Prompt hướng dẫn AI trả lời, sửa lỗi hiển thị và xử lý dữ liệu đầu vào.
*   **Thành:** Soạn câu hỏi test, viết code chấm điểm tự động và làm các file tài liệu hướng dẫn.

## 5. Kết luận
Nhóm đã hoàn thành đủ các bước của bài thực hành. Hệ thống trả lời tốt cả tiếng Việt lẫn các thuật ngữ kỹ thuật. Đây là bài học hay về việc kết hợp nhiều phương pháp tìm kiếm để có kết quả tốt nhất.

## 6. Kết quả Grading Questions
Sau khi nhận 10 câu hỏi từ giảng viên lúc 17:00, nhóm đã chạy máy và lấy kết quả. 

*   Cả 10 câu đều có câu trả lời, không bị lỗi khi chạy.
*   Kết quả đã được lưu tại file `logs/grading_run.json`.
*   Nhóm thấy AI trả lời khá tốt các câu hỏi khó về thời gian xử lý sự cố.

---
*Ngày hoàn thành: 13/04/2026*
