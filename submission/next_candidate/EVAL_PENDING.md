# Trạng thái eval bản loop-followup

## Kết quả đã có

Hai báo cáo dưới đây được tạo trên source commit `ca987f0c7a96b5fc91ce2cb2c4c8ff50960c6147`, dùng chung cấu hình OpenRouter `openai/gpt-4o-mini` cho agent và judge, snapshot, `workers=1`:

- `eval_next_candidate.json`: core đã chấm đủ 22/22, điểm **80.23/100**, `max_steps=8`.
- `eval_bonus_next_candidate.json`: bonus chấm được 9/10, partial mean **78.33**. Case B6 unscored vì model request bị ngắt kết nối (`WinError 10054`). Do chưa chấm đủ, `score_0_100` và `bonus_points_0_15` đều `null`; không dùng partial mean làm điểm bonus.

Trace cho thấy follow-up đã giúp H1/H6 gọi incident liên kết ở model step thứ hai; B3 báo lần đầu bị HTTP 429 rồi retry thành công; B4 dừng sau ba lần gọi Vercel. B10 lại gọi Vercel bốn lần và bị mechanical cap vì bộ đếm trước đó chỉ chặn ba lỗi 429 liên tiếp, reset sau khi tool thành công.

## Source hiện tại

Sau eval trên, `agent.py` được sửa để giới hạn tổng cộng tối đa ba lần gọi cùng tool/provider khi người dùng yêu cầu retry và nhắc model dừng sau khi retry thành công. Đây là thay đổi mới nhất; chưa có eval xác nhận. Source trong `submission/next_candidate/agent.py` vẫn là snapshot đã chạy ở commit `ca987f0`; source mới được lưu ở `submission/final_candidate/agent.py`.

## Chạy lại source mới

Đặt `OPENROUTER_API_KEY` trong process PowerShell hiện tại, không gửi key qua chat. Chạy tại thư mục gốc repo:

```powershell
$env:PYTHONUTF8 = "1"
& "C:\Users\qvinh\AppData\Local\Python\bin\python.exe" evals/run_evals.py --provider openrouter --model openai/gpt-4o-mini --judge-provider openrouter --judge-model openai/gpt-4o-mini --max-steps 8 --workers 1 --output eval_final.json
& "C:\Users\qvinh\AppData\Local\Python\bin\python.exe" evals/run_evals.py --bonus --provider openrouter --model openai/gpt-4o-mini --judge-provider openrouter --judge-model openai/gpt-4o-mini --max-steps 16 --workers 1 --output eval_bonus_final.json
```

Chỉ `eval_bonus_final.json` đủ 10/10 case mới có điểm tổng và bonus points hợp lệ. B6 ở lượt cũ là lỗi kết nối tạm thời; phải chạy lại full bonus để nhận điểm hợp lệ, không sửa tay hoặc ghép case vào kết quả cũ.

## Thông tin cá nhân còn thiếu

Thông tin chủ repo: **Tao Quang Vinh**, **2A202604081**, lớp **L3B**. `origin` hiện trỏ tới `https://github.com/qvinhh2312/K5-L3-Day4-ReactLoopAgent`; tên repo theo quy định là `K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent`, URL dự kiến `https://github.com/qvinhh2312/K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent`. Chưa xác nhận đổi tên trên GitHub hoặc nộp link LMS.
