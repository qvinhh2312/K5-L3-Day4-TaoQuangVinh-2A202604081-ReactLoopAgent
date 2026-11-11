# Status Investigation Agent — kết quả đánh giá

## Kiến trúc và độ bền

`run_agent()` gọi model theo từng step, giữ nguyên assistant message, thực thi mọi tool call theo thứ tự và trả lại đúng `tool_call_id`. Lỗi tool trở thành observation; lỗi provider, output bị cắt và hết step có trạng thái riêng. Trace ghi model/tool events, giữ trường bằng chứng thiết yếu và thu gọn dữ liệu lớn. Gate nguồn tầng 1 chỉ yêu cầu URL HTTP(S) từ `get_incident_details` thành công. Gate tầng 2 có cờ `strict_sources`, mặc định tắt.

At the core tag, **46/46 core tests** and **3/3 then-existing bonus adapter tests** passed. The separate optional bonus retry extension is documented in `BONUS_NOTES.md` and is not part of the core tag. On Windows, use the local Python executable with `PYTHONUTF8=1` to read UTF-8 snapshots.

`compare.py` kiểm tra số case, ID, expected/question/scenario, summary, cấu hình, manifest, hash file đóng băng, hash test cũ và xác nhận khác biệt code chỉ là prompt đã chọn. Chạy bằng `python compare.py` từ thư mục repo.

## Baseline và lựa chọn lỗi

Baseline dùng OpenRouter `openai/gpt-4o-mini` cho agent và judge, snapshot core, `max_steps=8`, `workers=1`. Đã chấm đủ 22/22 case, không có case `unscored`; điểm **77,27/100**.

Chọn **A5** (15/100). Câu hỏi yêu cầu danh sách đầy đủ incident GitHub Actions trong năm 2025. Trace chỉ có `get_status` với `component=Actions`; tool trả ghi chú rằng tìm trong 50 incident gần nhất và trả tối đa 5 mục. Answer baseline vẫn kết luận không có incident trong năm 2025, không đủ căn cứ để xác nhận điều đó.

Thay đổi duy nhất giữa các tag là system prompt: nêu rõ giới hạn 50 incident, giới hạn 5 kết quả, và cấm suy ra không có incident từ kết quả tìm kiếm hạn chế. Không bật gate nguồn tầng 2 vì A1, A8 và H1 đã có URL cho từng provider trong trace/answer.

## Before/after

| Case | Before | After | Delta |
|---|---:|---:|---:|
| E1 | 65 | 75 | +10 |
| E2 | 80 | 100 | +20 |
| E3 | 90 | 75 | -15 |
| E4 | 85 | 100 | +15 |
| E5 | 60 | 75 | +15 |
| E6 | 100 | 75 | -25 |
| A1 | 85 | 100 | +15 |
| A2 | 100 | 100 | 0 |
| A3 | 75 | 75 | 0 |
| A4 | 75 | 100 | +25 |
| A5 | 15 | 70 | +55 |
| A6 | 80 | 70 | -10 |
| A7 | 75 | 100 | +25 |
| A8 | 100 | 100 | 0 |
| H1 | 60 | 60 | 0 |
| H2 | 100 | 50 | -50 |
| H3 | 100 | 100 | 0 |
| H4 | 100 | 100 | 0 |
| H5 | 75 | 100 | +25 |
| H6 | 45 | 55 | +10 |
| H7 | 55 | 55 | 0 |
| H8 | 80 | 80 | 0 |

Tổng điểm **77,27 → 82,50** (+5,23), thấp hơn ngưỡng tăng 10 điểm đã định. Theo ngưỡng từng case, 10 case cải thiện, 4 case regression và 8 case không đổi. Tất cả 22 case đều được chấm ở cả hai lượt; không có trạng thái `error` hoặc `max_steps`.

| Chỉ số | Before | After |
|---|---:|---:|
| Model calls | 53 | 49 |
| Agent prompt tokens | 37.461 | 35.944 |
| Agent completion tokens | 10.022 | 8.257 |
| Judge prompt tokens | 42.822 | 33.780 |
| Judge completion tokens | 3.192 | 2.981 |
| Validation events | 2 | 3 |
| Judge trace truncated | 0 | 0 |
| Provider-reported cost | $0,019443 | $0,016683 |

Chi phí là tổng trường `cost` do provider ghi trong usage của agent và judge; không ngoại suy giá ngoài dữ liệu run.

## Kết luận, regression và giới hạn

A5 trong full after run tăng từ 15 lên 70, nhưng answer vẫn mở đầu bằng kết luận không có incident năm 2025 rồi mới nói dữ liệu không đủ để khẳng định. Một lượt A5 riêng sau cải tiến đạt 55/100 (`eval_results_a5_after.json`), cho thấy judge/model có dao động; không dùng lượt riêng đó thay kết quả full run.

Regression đáng chú ý nhất là **H2: 100 → 50**. After run bỏ `get_status` dù case yêu cầu tool này, tạo mechanical violation mới. E3 giảm 15, E6 giảm 25, A6 giảm 10. Đây có thể chịu ảnh hưởng của độ ngẫu nhiên model/judge, nhưng hiện là regression quan sát được và cần kiểm tra lại bằng lượt lặp. H1 vẫn thiếu tool calls ở hai model steps; H6 vẫn thiếu giải thích và mechanical check; H7 vẫn có câu khẳng định không đủ căn cứ sau timeout.

Đã chạy lặp các regression theo cùng cấu hình trên code `eval-after`: A6 **75** (so với baseline 80, giảm 5 nên không còn qua ngưỡng regression); E3 **75** (giảm 15); E6 **70** (giảm 30); H2 **50** (giảm 50, vẫn thiếu `get_status`). E3, E6 và H2 tiếp tục là regression quan sát được. Mỗi case mới chỉ có một lượt lặp.

Judge dùng cùng model với agent, một lượt eval cho mỗi phiên bản không chứng minh độ ổn định. Cần đối chiếu expected và trace, không coi điểm judge là kết luận tuyệt đối.

Baseline file được tạo trước khi commit/tag `eval-before`; tag được backfill sau đó từ đúng source state trước cải tiến. `eval_manifest_before.json` ghi rõ trạng thái này để không tuyên bố sai rằng baseline tree sạch tại thời điểm chạy. After eval được tạo sau commit/tag `eval-after` với cùng provider, model, judge, dataset, snapshot và giới hạn step. Hash các file đóng băng và test cũ giống nhau giữa hai tag.

Gate nguồn tầng 1 đã có trong cả hai phiên bản baseline/after. Eval snapshots được ghi ngày 2026-11-09; chúng không đại diện trạng thái live hiện tại.

## Bản ứng viên sau eval

Sau khi hoàn tất các lượt eval nêu trên, system prompt được bổ sung hướng dẫn cho các lỗi lặp lại: tra cả `get_status` và `get_incident_details` khi câu hỏi yêu cầu trạng thái hiện tại cùng incident cụ thể; tách trạng thái component khỏi trạng thái vòng đời incident; giữ trạng thái là chưa xác định khi tool lỗi; retry 429 tối đa ba lần khi người dùng yêu cầu; và lấy chi tiết incident mới nhất trước khi nêu phạm vi/cập nhật. Đây là thay đổi prompt trong source hiện tại, chưa được chạy eval lại vì terminal hiện không có `OPENROUTER_API_KEY`.

Vì vậy, điểm **82,50/100** và kết quả bonus **74/100 (11,1/15)** ở trên thuộc về source đã đánh giá trước bản ứng viên này, không phải điểm xác nhận cho source hiện tại. Cần chạy lại đủ 22 case core và 10 case bonus với cùng cấu hình trước khi ghi nhận điểm mới.
