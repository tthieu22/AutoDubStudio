# Rule: Bắt buộc duy trì và cập nhật PROJECT_OVERVIEW.md

## Mục đích
Đảm bảo mọi AI Assistant hoặc developer khi tiếp quản hoặc làm việc trong dự án AutoDubStudio luôn nắm rõ bức tranh toàn cảnh, kiến trúc hệ thống và tiến độ hiện tại mà không bị mất bối cảnh hay hiểu nhầm domain.

## Quy định bắt buộc:
1. **Đọc tổng quan trước khi thực thi**: Trước khi tiến hành sửa đổi các tính năng lớn, AI phải kiểm tra [`PROJECT_OVERVIEW.md`](file:///d:/FullStack/AutoDubStudio/PROJECT_OVERVIEW.md) để hiểu rõ kiến trúc tổng thể.
2. **Cập nhật ngay sau khi thay đổi**: Khi hoàn thành bất kỳ nhiệm vụ nào liên quan đến:
   - Thêm/bớt/sửa đổi module hoặc component mới.
   - Refactor file nguồn hoặc thay đổi cấu trúc thư mục.
   - Thay đổi các Specialized Prompt Engines hoặc logic Fail-Closed validation.
   - Bổ sung các lệnh IPC Rust backend hoặc giao diện.
   
   AI **BẮT BUỘC** phải cập nhật lại thông tin vào [`PROJECT_OVERVIEW.md`](file:///d:/FullStack/AutoDubStudio/PROJECT_OVERVIEW.md) (hoặc các tài liệu chuyên sâu trong thư mục `docs/`) và ghi nhận dòng nhật ký mới vào bảng **Progress Change Log**.
3. **Giữ tài liệu ngắn gọn, dễ tra cứu**: Nếu file vượt quá độ dài khuyến nghị, tách các phần chi tiết sang thư mục `docs/` và liên kết từ `PROJECT_OVERVIEW.md`.
