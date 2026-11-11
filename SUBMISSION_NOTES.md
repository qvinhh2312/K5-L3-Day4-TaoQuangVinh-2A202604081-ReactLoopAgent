# Status Investigation Agent — kết quả đánh giá

**Họ và tên:** Tao Quang Vinh
**MSSV:** 2A202604081
**Lớp:** L3B
**Tên repo cần dùng:** `K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent`

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

Vì vậy, điểm **82,50/100** và kết quả bonus **74/100 (11,1/15)** ở trên thuộc về source đã đánh giá trước bản ứng viên này. Các lượt chạy xác nhận trên source mới được ghi ở mục tiếp theo.

## Đánh giá bản ứng viên

Đã chạy lại đủ core và bonus trên source commit `866e127b5eb00a853de6ae2f2a04d0704747e8bf`, với cùng OpenRouter `openai/gpt-4o-mini`, judge model và `max_steps` như các lượt trước. Core được chấm 22/22, đạt **79,55/100**; bonus 10/10, đạt **73,7/100 (11,05/15)**.

Core candidate giảm 2,95 điểm so với `eval_after.json` (82,50), nhưng vẫn cao hơn baseline 77,27. H2 tăng từ 50 lên 100 và không còn thiếu `get_status`; A5 tăng 5, A6 tăng 5. E3 và E6 giữ nguyên lần lượt 75. Một số case giảm đáng kể: E1 75→60, E2 100→75, A7 100→70, A8 100→75, H4 100→80. H1 và H6 vẫn vi phạm yêu cầu gọi tool ở nhiều model step.

Kết quả cho thấy thêm chỉ dẫn giải quyết được lỗi chọn tool của H2 nhưng làm điểm tổng thấp hơn do chất lượng dao động ở nhiều case; đây chưa phải một cải thiện tổng thể. Chi tiết theo case nằm trong `eval_candidate.json`.

## Bản tiếp theo đang chờ eval

Sau lượt candidate, `agent.py` được cập nhật để khi câu hỏi yêu cầu rõ ràng, loop sẽ gửi model một nhắc việc có căn cứ từ trace: gọi lại tool sau HTTP 429 theo giới hạn, nêu lần rate limit nếu retry thành công, tra `get_incident_details` cho incident mới nhất tìm được qua status, và theo URL incident liên quan trước khi trả lời. Loop không tự gọi tool thay model. Bản này chưa được eval; các điểm candidate ở mục trên không áp dụng cho thay đổi mới nhất.

Tại thời điểm ghi mục này, lượt eval chưa chạy được trong process làm việc vì thiếu `OPENROUTER_API_KEY`. Kết quả do người dùng chạy sau đó được ghi ở mục dưới.

## Eval loop-followup và giới hạn retry

Kết quả trên commit `ca987f0c7a96b5fc91ce2cb2c4c8ff50960c6147`:

- Core: **80.23/100, 22/22**, cùng cấu hình OpenRouter `openai/gpt-4o-mini`, judge cùng model, `max_steps=8`.
- Bonus: **9/10 scored, 1 unscored**, partial mean **78.33**. Vì B6 gặp lỗi kết nối `[WinError 10054]`, `score_0_100` và `bonus_points_0_15` là `null`; không thể báo điểm bonus hoàn chỉnh.
- H1/H6 đều đạt hai model steps, không còn mechanical violation. B3 nêu rõ 429 rồi retry thành công. B4 gọi Vercel ba lần rồi bị chặn lần gọi kế tiếp.
- B10 vượt giới hạn ba lần gọi Vercel: lần gọi thành công reset bộ đếm liên tiếp, khiến model tiếp tục gọi. Đây là lỗi giới hạn ở retry state.

Ngay sau eval này, `agent.py` được sửa để đếm tối đa ba lần gọi tổng cộng cho câu hỏi yêu cầu retry rõ ràng và yêu cầu dừng sau lần retry thành công. Tại thời điểm đó thay đổi chưa được chấm; lượt full eval sau trên commit `16290ee` được ghi bên dưới.

## Full eval sau giới hạn retry

Đã chạy đủ hai bộ trên source commit `16290eea43d14595f57dc8374f7a0bcb22ba77d0`, cùng OpenRouter `openai/gpt-4o-mini` cho agent/judge, snapshot, `workers=1`:

- Core: **87.95/100 (22/22)**, `max_steps=8`.
- Bonus: **76.5/100 (10/10)**, quy đổi **11.47/15**, `max_steps=16`.
- B6 được chấm 80; B10 70 và không vượt cap số lần gọi.
- Điểm thấp còn lại: B7 45 (incident history không cần thiết, judge đánh dấu ngày/status sai) và B9 30 (không nêu rõ Linear/Slack không được hỗ trợ, trả thêm provider khác).

Họ tên, MSSV và lớp đã được điền ở đầu ghi chú. `origin` hiện là `https://github.com/qvinhh2312/K5-L3-Day4-ReactLoopAgent`; repo cần đổi thành `K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent`. URL dự kiến sau đổi tên là `https://github.com/qvinhh2312/K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent`. Việc đổi tên GitHub và trạng thái nộp LMS chưa được xác nhận. Eval files giữ nguyên theo output chạy; không ghép tay hoặc sửa kết quả chấm.

## Prompt candidate cho B7/B9

Sau full eval trên, system prompt được bổ sung hướng dẫn trả lời đúng phạm vi provider/thời điểm được hỏi và nêu rõ khi provider không có tích hợp. Source mới nằm trong `submission/pending_prompt_candidate/`; nó chưa được eval. Kết quả **87.95/100** và **76.5/100 (11.47/15)** ở trên chỉ áp dụng cho source commit `16290eea43d14595f57dc8374f7a0bcb22ba77d0`. Cần chạy hai lệnh trong `submission/pending_prompt_candidate/EVAL_PENDING.md` để đo candidate mới.
