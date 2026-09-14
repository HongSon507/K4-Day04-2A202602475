# Danh sách thành viên và Quá trình đóng góp — Nhóm Day 04 Lab

## Thông tin thành viên nhóm

| Họ và tên | MSSV | GitHub Username | Vai trò chính |
| :--- | :--- | :--- | :--- |
| **Trần Hồng Sơn** | 2A202602475 | `HongSon507` | **Captain (Nhóm trưởng)** |
| **Đinh Đức Thái** | 2A202602648 | `ducthais` | **Member** |
| **Đàm Quang Sơn** | 2A202602868 | `KuanqXol` | **Member** |

---

## Quá trình làm việc và Phân công theo từng Commit

Quy trình phát triển và tối ưu hóa hệ thống IT Helpdesk Agent được chia thành các giai đoạn rõ ràng, gắn liền với các commit và phiên bản trong Git history:

### Giai đoạn 1: Khởi tạo dự án & Đánh giá Baseline (`v0`)
* **Thành viên phụ trách:** Trần Hồng Sơn (`HongSon507`)
* **Nội dung thực hiện:**
  - Khởi tạo fork chung của nhóm từ repository nguồn VinUni-AI20k.
  - Cấu hình môi trường (`.venv`, các thư viện phụ thuộc, kiểm tra smoke test).
  - Chạy đánh giá đo lường phiên bản ban đầu `v0` trên bộ test `eval_base.json` (chưa chỉnh sửa prompt/tools).
  - Ghi nhận kết quả baseline: 20/30 cases đạt (66.67%), phát hiện các nhóm lỗi chính: `wrong_tool`, `missing_info`, `wrong_boundary`.
* **Commit đại diện:**
  - `add files` / `init repo and environment`

---

### Giai đoạn 2: Cải tiến Phiên bản `v1` (Khắc phục lỗi Tool Routing & Tham số)
* **Thành viên phụ trách:** Trần Hồng Sơn (`HongSon507`)
* **Nội dung thực hiện:**
  - Phân tích nguyên nhân lỗi tại **H03** (`search_kb`) và **H04** (`lookup_user`):
    - H03: Model bỏ quên tham số `category` khi tìm kiếm giải pháp Outlook.
    - H04: Model gọi thừa `inspect_device(asset_id="EMP-1003")` do nhầm lẫn giữa thiết bị được cấp và chẩn đoán tài sản.
  - Chỉnh sửa `starter_v0/artifacts/tools.yaml`: Thêm ràng buộc `category` bắt buộc cho `search_kb`, làm rõ `lookup_user` đã trả về danh sách thiết bị được cấp, giới hạn phạm vi `inspect_device`.
  - Bổ sung quy tắc định tuyến toàn cục trong `starter_v0/artifacts/system_prompt.md`.
  - Chạy đánh giá `v1`: Tăng tỷ lệ đạt từ **20/30 lên 24/30 (80.0%)**, sửa thành công H03, H04, H13, H18 với 0 regression.
* **Commit đại diện:**
  - `60d2369: fix case H03 H04 : wrong tools`

---

### Giai đoạn 3: Cải tiến Phiên bản `v2` (Xử lý Missing Info & Ranh giới Xác nhận)
* **Thành viên phụ trách:** Đinh Đức Thái (`ducthais`)
* **Nội dung thực hiện:**
  - Tập trung giải quyết 6 failure cases còn lại ở `v1`:
    - Nhóm `missing_info` (H10, H11, H19): Xử lý các tình huống thiếu mã tài sản (`asset_id`), thiếu mã nhân viên (`employee_id`), hoặc môi trường không rõ ràng.
    - Nhóm `wrong_boundary` (H12, M05, M09): Xử lý hành động ghi trạng thái nhạy cảm (`create_ticket`) và vô hiệu hóa xác nhận cũ khi thông tin bị thay đổi.
  - Cập nhật `system_prompt.md`:
    - Bắt buộc gọi `clarify(response_type="text")` khi thiếu ID, nghiêm cấm tự đoán mò mã tài sản/nhân viên.
    - Yêu cầu xác nhận rõ ràng `clarify(response_type="yes_no")` trước khi tạo ticket.
    - Xử lý lựa chọn môi trường `clarify(response_type="choice")` cho staging/production.
  - Chạy đánh giá `v2`: Đạt điểm số tuyệt đối **30/30 cases (100%)** trên toàn bộ `eval_base.json`.
* **Commit đại diện:**
  - `753dda0: Fix testcase remaining v2 v3`

---

### Giai đoạn 4: Phiên bản `v3` (Mở rộng tính năng, Bảo mật Adversarial & Báo cáo)
* **Thành viên phụ trách:** Đàm Quang Sơn (`KuanqXol`) & Cả nhóm
* **Nội dung thực hiện:**
  - Mở rộng phạm vi cho các tool nâng cao: `policy` (tra cứu chính sách IT nội bộ), `create_ticket` (tạo ticket sau xác nhận), `search_device_info` (tìm kiếm thông tin thiết bị công khai trên web).
  - Kiểm thử và đánh giá bộ an toàn bảo mật `eval_adversarial.json` (chống prompt injection, không rò rỉ dữ liệu nội bộ ra web search).
  - Thiết kế bộ 10 test cases riêng của nhóm trong `starter_v0/data/eval_group.json` (5 single-turn và 5 multi-turn).
  - Hoàn thiện tài liệu báo cáo nghiệm thu `starter_v0/artifacts/REPORT.md` và kiểm tra `version_log.csv`.
* **Commit đại diện:**
  - `feat(eval): add team eval group cases and adversarial evidence`
  - `docs(report): complete final report and submission deliverables`

---

## Checklist xác nhận trước khi nộp bài

- [x] Repository fork chung hoạt động bình thường, đúng cấu trúc.
- [x] File `TEAMMATES.md` có đầy đủ Họ tên, MSSV, GitHub Username và phân công công việc.
- [x] Mỗi thành viên có ít nhất 1 commit riêng đã được merge vào branch nộp bài.
- [x] Không commit file `.env`, API key, `.venv`, cache hay dữ liệu nhạy cảm.
- [x] Toàn bộ artifact (`system_prompt.md`, `tools.yaml`, `version_log.csv`, `REPORT.md`) đã sẵn sàng.
- [ ] Tất cả thành viên nộp cùng một link repository fork chung trên VLearn.
