# Ghi chú phân tích · Day 04

Họ và tên: Tao Quang Vinh
MSSV: 2A202604081
Lớp: L3B
Tên repo cần dùng: `K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent`
Remote hiện tại: `https://github.com/qvinhh2312/K5-L3-Day4-ReactLoopAgent`
URL dự kiến sau khi đổi tên: `https://github.com/qvinhh2312/K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent` (chưa xác nhận)

## 1. Case được chọn

- ID case: A5.
- Câu hỏi: cần danh sách đầy đủ mọi incident GitHub Actions trong năm 2025, đồng thời yêu cầu nói rõ độ đầy đủ và không bịa.
- Điểm lần chạy 1: 15/100 (`eval_before.json`).

## 2. Bằng chứng trong trace

Trace A5 của lần chạy 1 ghi lại một lần gọi `get_status` với `provider=github`, `component=Actions`. Tool trả về `matching_incidents_in_last_50: 23` và ghi chú: “Chỉ tìm theo chuỗi trong 50 incident gần nhất; không tìm thấy không chứng minh không có sự cố.” Kết quả cũng chỉ trả tối đa 5 incident gần đây; các ví dụ hiện ra được cập nhật trong tháng 11/2026.

Dù vậy, câu trả lời baseline khẳng định “không có sự cố nào liên quan đến GitHub Actions trong năm 2025 được ghi nhận” và kết luận “Không có sự cố ... nào ... trong năm 2025.” Snapshot 50 incident gần nhất không bao phủ đủ dữ liệu để kết luận như vậy. Judge cho A5 điểm factuality 0, boundaries 0; lý do chính là khẳng định không có incident mà thiếu bằng chứng và không đáp ứng yêu cầu độ đầy đủ.

```text
Tool: get_status(provider="github", component="Actions")
Tool note: chỉ tìm trong 50 incident gần nhất; không tìm thấy không chứng minh không có sự cố.
Baseline answer: “Không có sự cố GitHub Actions nào được ghi nhận trong năm 2025.”
```

## 3. Thay đổi đã thực hiện

- Sửa system prompt trong `agent.py`: nêu rõ giới hạn snapshot 50 incident gần nhất và tối đa 5 kết quả; yêu cầu không suy ra rằng không có incident từ kết quả tìm kiếm giới hạn.
- Chọn thay đổi này vì trace cho thấy tool đã cung cấp giới hạn dữ liệu nhưng câu trả lời vẫn kết luận quá mức. Vấn đề nằm ở cách agent diễn giải và trình bày bằng chứng, không phải thiếu dữ liệu trong fixture.

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---:|---:|
| Điểm tổng | 77.27/100 (22/22 case) | 82.50/100 (22/22 case) |
| Điểm A5 | 15/100 | 70/100 |
| Số model calls | 53 | 49 |
| Agent tokens (prompt/completion) | 37,461 / 10,022 | 35,944 / 8,257 |
| Provider-reported cost tổng | $0.019443 | $0.016683 |

- Lỗi được cải thiện: A5 tăng 55 điểm; câu trả lời sau thay đổi thừa nhận không thể cung cấp danh sách đầy đủ năm 2025 từ snapshot giới hạn.
- Lỗi còn lại hoặc mới xuất hiện: câu trả lời A5 của full run vẫn mở đầu bằng kết luận không có incident năm 2025 rồi mới nói dữ liệu không đủ; judge ghi nhận thông tin incident có thể không liên quan năm 2025. H2 giảm từ 100 xuống 50 và thiếu gọi `get_status`; các lần lặp cho thấy E3, E6 và H2 tiếp tục thấp hơn baseline. Chi tiết và giới hạn số lần lặp được ghi trong `SUBMISSION_NOTES.md`.

## 5. Giới hạn

Điểm judge là ước lượng từ model, không phải xác nhận tuyệt đối về chất lượng. Snapshot dữ liệu được tạo ngày 2026-11-09 và chỉ gồm tối đa 50 incident gần nhất, nên không thể dùng để khẳng định danh sách lịch sử đầy đủ cho năm 2025. Mỗi phiên bản core có một full run; các lần chạy lặp chỉ tập trung vào A6/E3/E6/H2 và mỗi case có một lần lặp, nên kết quả cho thấy dấu hiệu dao động nhưng chưa đủ để ước lượng ổn định dài hạn. Baseline tag được backfill từ đúng source state sau khi eval baseline chạy; manifest ghi rõ điều này.

Sau các lượt eval đã ghi ở trên, system prompt được bổ sung thêm hướng dẫn về đối chiếu status với incident cụ thể, phân biệt trạng thái component với incident, xử lý timeout/429 và tra chi tiết incident mới nhất. Bảng before/after ở trên vẫn giữ nguyên kết quả lịch sử của hai phiên bản đó; kết quả chấm source ứng viên mới được ghi bên dưới.

### Lượt đánh giá bản ứng viên

Sau đó, đã chạy đủ 22 case core và 10 case bonus trên commit `866e127b5eb00a853de6ae2f2a04d0704747e8bf`, cùng cấu hình model/judge và giới hạn bước như trước:

| Chỉ số | `eval_after.json` | Bản ứng viên |
|---|---:|---:|
| Core | 82.50/100 (22/22) | 79.55/100 (22/22) |
| Bonus | 74.0/100 (11.10/15) | 73.7/100 (11.05/15) |
| H2 | 50 | 100 |
| E3 / E6 | 75 / 75 | 75 / 75 |
| B6 / B10 | 50 / 50 | 50 / 50 |

Prompt mới sửa được lỗi thiếu `get_status` ở H2, nhưng điểm core tổng giảm 2.95; bonus giảm 0.3. B6 vẫn không gọi `get_incident_details`, B10 vẫn chỉ gọi Vercel một lần sau 429, còn B3 vẫn không nói rõ lần gọi đầu bị rate limit. Bản ứng viên chưa phải cải thiện tổng thể. Kết quả chi tiết nằm trong `eval_candidate.json` và `eval_bonus_candidate.json`.

Sau lượt đó, `agent.py` được cập nhật thêm cơ chế nhắc model dựa trên trace để hoàn tất retry được yêu cầu và tra incident mới nhất/liên kết trước khi trả lời. Tại thời điểm đó bản mới chưa được chấm; lượt eval chạy sau trên commit `ca987f0` được ghi bên dưới. Điểm candidate trong bảng không áp dụng cho code sau này.

### Eval bản loop-followup

Sau đó đã xuất hiện `eval_next_candidate.json` và `eval_bonus_next_candidate.json`, được chạy trên source commit `ca987f0c7a96b5fc91ce2cb2c4c8ff50960c6147` với cùng OpenRouter model/judge, core `max_steps=8`, bonus `max_steps=16`, `workers=1`.

| Tập | Kết quả | Trạng thái |
|---|---:|---|
| Core | 80.23/100 (22/22) | Đã chấm đủ |
| Bonus | 9 case đã chấm, 1 chưa chấm; partial mean 78.33 | Điểm tổng và bonus points là `null` |

Follow-up đã giúp H1/H6 đủ hai model step (đều 80 điểm, không còn mechanical violation), B3 nêu được lần đầu bị 429 rồi retry thành công (75), B4 dừng sau ba lần Vercel bị giới hạn (85). B6 bị `WinError 10054` khi model gọi tiếp sau các nhắc việc; case chưa được chấm, không được tính như điểm 0. B10 có bốn tool calls Vercel vì loop reset bộ đếm sau khi một retry thành công; mechanical check giới hạn tối đa ba lần nên case bị cap 50.

Sau lượt này, loop được sửa để giới hạn tổng số lần gọi là ba khi user yêu cầu retry và nhắc model dừng sau khi retry thành công. Bản sửa mới này **chưa được eval**. Link repo GitHub đã đổi tên và trạng thái nộp LMS chưa có trong workspace.

### Kết quả cho commit `ca987f0`

Core được chấm đủ 22/22, đạt **80.23/100**. H1/H6 đạt yêu cầu hai model step, mỗi case 80 điểm; H2 đạt 90. Bonus chỉ chấm đủ 9/10, partial mean 78.33, không có điểm tổng hoặc điểm bonus hợp lệ vì B6 gặp lỗi kết nối `[WinError 10054]`. B10 bị cap 50 do bốn lần gọi Vercel. Những kết quả này áp dụng cho commit `ca987f0`, trước sửa giới hạn tổng lần gọi.

Code sau sửa được lưu tại `submission/final_candidate/`; chưa có kết quả eval của bản đó. Thông tin cá nhân đã được điền ở đầu file. Remote `origin` vẫn trỏ tới tên repo cũ nêu trên; tên và URL đích đã ghi ở đầu file. Chưa xác nhận việc đổi tên GitHub hay nộp LMS.
