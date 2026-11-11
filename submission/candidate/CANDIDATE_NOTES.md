# Kết quả đánh giá bản ứng viên

Source được đánh giá: commit `866e127b5eb00a853de6ae2f2a04d0704747e8bf`.

Cấu hình cả hai lượt: OpenRouter `openai/gpt-4o-mini` làm agent và judge; snapshot dataset; core `max_steps=8`, bonus `max_steps=16`, `workers=1`.

- Core: 22/22 case, 79.55/100.
- Bonus: 10/10 case, 73.7/100, tương đương 11.05/15.

Core score cao hơn baseline 77.27 nhưng thấp hơn lượt `eval_after.json` 82.50. H2 cải thiện 50→100; E3/E6 không đổi 75/75. H1/H6 vẫn có mechanical violation. B6 vẫn thiếu `get_incident_details`; B10 vẫn chỉ gọi Vercel một lần sau 429. Bonus tổng giảm 74.0→73.7. Đây là kết quả của lượt chạy đơn cho mỗi full dataset; judge và model có tính dao động.

Các file JSON là nguyên bản do `evals/run_evals.py` tạo. Gói này giữ tách biệt với tag `core-submission`, vốn vẫn trỏ tới code đã đạt 82.50 trong lần core trước đó.
