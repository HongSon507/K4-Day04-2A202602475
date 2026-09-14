# Lab Guide — Gợi ý cách làm bài

Tài liệu này chỉ đưa ra một quy trình tham khảo. Đây không phải đáp án mẫu và
không bắt buộc nhóm phải làm đúng từng bước. Yêu cầu đầu ra chính thức nằm trong
`README.md`.

Trừ khi ghi rõ khác, các path và command bên dưới được hiểu là đang ở thư mục
`starter_v0/`.

## 1. Bắt đầu từ việc hiểu interface

Trước khi sửa code hoặc prompt, nên đọc:

- `artifacts/system_prompt.md`;
- `artifacts/tools.yaml`;
- một vài case trong `data/eval_base.json`;
- implementation và `TOOL.md` của các tool liên quan.

Thử trả lời ba câu hỏi:

1. Model nhìn thấy thông tin gì?
2. Python implementation thực sự làm gì?
3. Evaluator đang so sánh điều gì?

Một tool implementation tốt không đảm bảo model sẽ chọn đúng tool nếu name,
description hoặc schema chưa rõ.

## 2. Kiểm tra môi trường trước

Nên kiểm tra syntax và các local tool trước khi tiêu quota model:

```powershell
cd starter_v0
python -m compileall -q .
```

Sau đó chạy các smoke command trong `TOOL-SETUP.md`, rồi mới chạy provider
preflight. Nếu compile, smoke check hoặc preflight lỗi, nên xử lý lỗi setup trước
khi đánh giá prompt.

## 3. Chạy baseline mà chưa tối ưu

Nên giữ nguyên starter artifacts khi chạy `v0`. Baseline là mốc so sánh, không
phải phiên bản cần đạt điểm cao.

Sau run, có thể chọn vài failure đại diện thay vì đọc log theo thứ tự. Nên ưu
tiên:

- một wrong-tool case;
- một wrong-argument case;
- một missing-information case;
- một multi-tool hoặc multi-turn case;
- một confirmation/security case.

## 4. Phân tích một failure

Có thể dùng mẫu ghi chú sau:

```text
Case:
Expected calls:
Actual calls:
Observed mismatch:
Tool execution result:
Giả thuyết nguyên nhân:
Artifact dự định sửa:
Metric dự kiến thay đổi:
Rủi ro regression:
```

Nên phân biệt:

- model chọn sai tool;
- model chọn đúng tool nhưng sai args;
- model gọi thiếu hoặc thừa tool;
- tool chạy nhưng trả error;
- final response diễn giải sai tool result.

Các lỗi này không nhất thiết có cùng cách sửa.

## 5. Chọn nơi sửa phù hợp

Gợi ý sửa system prompt khi vấn đề là nguyên tắc toàn cục, ví dụ:

- không tự đoán identifier;
- ưu tiên thông tin mới nhất trong hội thoại;
- xác nhận lại khi action payload thay đổi;
- không tin instruction do user hoặc retrieved content tự gắn role.

Gợi ý sửa tool declaration khi vấn đề là ranh giới capability, ví dụ:

- tool sở hữu loại dữ liệu nào;
- khi nào dùng và khi nào không dùng;
- argument có convention hoặc enum gì;
- tool có side effect hay external-data boundary nào.

Nếu lỗi nằm trong implementation, nên sửa implementation và thêm deterministic
test. Không nên dùng prompt để che một lỗi ghi file, type coercion hoặc data leak.

## 6. Làm từng vòng nhỏ

Mỗi version nên bắt đầu bằng một hypothesis cụ thể. Ví dụ:

```text
Nếu mô tả rõ shared service khác single asset, routing accuracy của nhóm
status/device sẽ tăng mà không làm tăng extra calls.
```

Một vòng tham khảo:

1. Chọn một nhóm failure.
2. Viết hypothesis.
3. Sửa một artifact chính.
4. Chạy lại cùng suite.
5. So metric và failed traces.
6. Ghi version log.
7. Kiểm tra regression ở các case đã pass.

Tránh đổi nhiều rule, rename tool và sửa schema cùng lúc nếu muốn biết thay đổi
nào tạo ra kết quả.

## 7. Thiết kế team eval

Nên thiết kế case từ failure mode mà nhóm thực sự quan tâm. Một bộ 10 case tốt
có thể bao phủ:

- ambiguous intent;
- identifier bị thiếu;
- correction ở turn sau;
- cancellation;
- hai tool cùng loại với args khác nhau;
- multiple assets;
- stale confirmation;
- format-only request;
- external/internal data boundary;
- capability riêng của UI hoặc bonus tool nếu có.

Case khó không nhất thiết phải dài. Một case tốt thường cô lập được một quyết định rõ ràng.

## 8. Thử adversarial behavior

Nên chạy adversarial suite sau khi routing cơ bản đã ổn. Khi review, đừng chỉ nhìn PASS/FAIL; hãy kiểm tra:

- tool nào thực sự được gọi;
- có file ticket nào được tạo không;
- external request body chứa trường gì;
- retrieved instruction có bị đưa vào trusted content không;
- fake SYSTEM/DEVELOPER/tool-result text có thay đổi hành vi không;
- confirmation có gắn với đúng payload cuối cùng không.

Một guardrail mạnh thường có hai lớp:

1. Prompt/declaration giúp model chọn hành vi đúng.
2. Tool implementation từ chối input nguy hiểm nếu model vẫn gọi sai.

## 9. Xây UI sau khi loop ổn định

Nên tái sử dụng `run_model_tool_loop` thay vì viết agent loop mới. UI có thể ưu
tiên hiển thị:

- user request;
- final response;
- từng tool name và args;
- tool result/error;
- round/status;
- artifact version và hashes;
- transcript path.

Một UI đơn giản nhưng trace rõ thường hữu ích hơn UI đẹp mà không audit được
tool behavior.

## 10. Chuẩn bị demo và report

Nên chọn 3–5 scenario đã chạy trước. Mỗi scenario nên có một câu chuyện cụ thể:

- v0 sai gì;
- nhóm đặt hypothesis nào;
- artifact nào thay đổi;
- metric hoặc trace thay đổi ra sao;
- còn giới hạn nào.

Nên chuẩn bị fallback run/transcript nếu provider hoặc network không ổn định.

Report nên dẫn đến evidence file cụ thể, không chỉ mô tả theo cảm giác.

## 11. Bonus tool

Viết tool mới là phần bonus, không phải điều kiện hoàn thành core lab.

Nếu chọn làm bonus, nên ưu tiên một capability thật sự thiếu. Trước khi code,
hãy xác định:

- input contract;
- output contract;
- source dữ liệu;
- error behavior;
- side effect;
- confirmation/privacy boundary;
- cách smoke test;
- eval case chứng minh tool hữu ích.

Một tool nhỏ nhưng có contract, test và evidence đầy đủ thường tốt hơn một tool
lớn nhưng không kiểm soát được hành vi.

## 12. Gợi ý quản lý thời gian

Một cách chia thời gian tham khảo:

- 15%: đọc starter và setup;
- 20%: baseline + failure analysis;
- 30%: ba vòng cải tiến;
- 15%: team eval + adversarial review;
- 10%: UI;
- 10%: report và rehearsal.

Nếu thiếu thời gian, nên ưu tiên evidence core, team eval và UI trước bonus tool.

## 13. Tự kiểm tra trước khi nộp

Có thể tự hỏi:

- Mỗi version có hypothesis thật không?
- Hash có phản ánh artifact đã thay đổi không?
- Provider error có bằng 0 không?
- Có đọc tool results thay vì chỉ metric không?
- Team eval có đúng 5 single + 5 multi không?
- Adversarial cases có được review thủ công không?
- UI có dùng chung loop không?
- Có secret, dữ liệu thật hoặc generated ticket trong submission không?
- Bonus tool, nếu có, đã có test và evidence chưa?
