# GrowthOS — Case study DA × BA × BD

> Một case study mô phỏng công ty thật, làm theo nhóm 3 vai: **Data Analyst (DA)**, **Business Analyst (BA)**, **Business Development (BD)**.
> Mỗi vai có phần việc riêng, nhưng **kết luận cuối cùng chỉ đúng khi cả 3 vai ghép lại với nhau**.
> Đề chỉ cho bối cảnh và dữ liệu. Đáp án là của nhóm bạn.

---

## 1. Bối cảnh

**GrowthOS** (công ty giả lập) là startup SaaS Việt Nam, bán phần mềm **quản lý bán hàng (POS) + kho** cho cửa hàng nhỏ và vừa:
tiệm tạp hoá/bán lẻ, quán cà phê/nhà hàng (F&B), spa/salon (Beauty), nhà thuốc (Pharmacy).

| Gói | Giá / tháng | Dành cho |
|---|---|---|
| Basic | 199.000đ (điều chỉnh từ 04/2025) | 1 cửa hàng |
| Pro | 499.000đ × số cửa hàng | 2–4 cửa hàng |
| Enterprise | 1.200.000đ × số cửa hàng | chuỗi từ 5 cửa hàng |

Khách đến từ 4 kênh: **Ads** (quảng cáo Facebook/Google), **Organic** (SEO, giới thiệu), **Sales** (đội sale gọi trực tiếp), **Partner** (ngân hàng, nhà phân phối, công ty kế toán giới thiệu khách, nhận hoa hồng).

### Email của CEO gửi nhóm bạn (tháng 01/2026)

> Chào cả nhóm,
>
> Năm 2025 MRR vẫn tăng, nhưng anh thấy không ổn: chi marketing tăng mạnh mà số khách mới không tăng tương xứng,
> giữa năm có giai đoạn khách huỷ nhiều bất thường, và đội sale than là mất deal chuỗi lớn vì "thiếu tính năng".
>
> Hội đồng quản trị muốn trong **2 quý tới** công ty chọn **một trọng tâm tăng trưởng** để dồn nguồn lực. Ba hướng đang được bàn:
> 1. Giảm churn (giữ khách đang có),
> 2. Đẩy mạnh kênh/phân khúc mới,
> 3. Đầu tư sản phẩm để thắng deal chuỗi lớn.
>
> Anh cần các em trả lời: **chuyện gì đã xảy ra năm 2025, vì sao, và GrowthOS nên dồn lực vào đâu**. Có số liệu, có giải pháp cụ thể, có kế hoạch triển khai.
> Ngân sách bổ sung tối đa: **1,5 tỷ đồng** cho 2 quý.
>
> Anh Tuấn — CEO

---

## 2. Dữ liệu

Dữ liệu giả lập từ **01/2024 đến 12/2025**, nằm trong `data/raw/` (đã sinh sẵn, mở được bằng Excel/Google Sheets/SQL/Python).

> ⚠️ **Không đọc `data/generate_data.py`** — file đó chứa các quy luật được cài vào dữ liệu, đọc là lộ đáp án.
> Nếu muốn sinh lại dữ liệu: `python3 data/generate_data.py`.

| File | Mỗi dòng là | Cột chính |
|---|---|---|
| `customers.csv` | 1 khách hàng | `customer_id`, `signup_date`, `segment`, `city`, `city_tier` (1 = thành phố lớn → 3 = tỉnh), `store_count_at_signup`, `acquisition_channel`, `partner_id`, `onboarding_completed` (0/1), `payment_method` |
| `subscriptions_monthly.csv` | 1 khách × 1 tháng | `month`, `plan`, `store_count`, `mrr_vnd`, `payment_failed` (0/1), `status` (`active` / `churned` = huỷ trong tháng đó) |
| `usage_monthly.csv` | 1 khách × 1 tháng | `active_days`, `transactions`, `features_used`, `staff_accounts` |
| `support_tickets.csv` | 1 ticket hỗ trợ | `created_date`, `category`, `resolution_hours`, `csat` (1–5) |
| `marketing_spend.csv` | 1 kênh × 1 tháng | `channel`, `spend_vnd` (riêng Partner = hoa hồng + chi phí quản lý) |
| `leads.csv` | 1 deal chuỗi (pipeline BD, 2025) | `source`, `segment`, `store_count`, `stage`, `est_mrr_vnd`, `closed_date`, `lost_reason`, `owner` |
| `partners.csv` | 1 đối tác | `partner_id`, `name`, `type`, `city`, `commission_rate` |

Dữ liệu có chủ ý **không sạch hoàn toàn về mặt nghiệp vụ** — việc định nghĩa chỉ số (churn tính thế nào, CAC gồm gì, LTV ước lượng ra sao…) là một phần của bài.

---

## 3. Nhiệm vụ theo vai

### 📊 DA — "Chuyện gì đã xảy ra?"
1. Xây bộ **chỉ số sức khoẻ**: MRR, tăng trưởng MRR (new / expansion / churned), số khách active, logo churn & revenue churn, ARPA.
2. **Cohort retention** theo tháng đăng ký; so sánh theo `segment`, `city_tier`, `acquisition_channel`, `onboarding_completed`.
3. **CAC và LTV theo kênh** → kênh nào đáng tiền, kênh nào đang "đốt" tiền.
4. Tìm và giải thích **các điểm bất thường** trong năm 2025 (có bao nhiêu? xảy ra khi nào? nhóm khách nào bị ảnh hưởng?).
5. Tìm **tín hiệu sớm** dự báo khách sắp huỷ (từ usage, ticket, thanh toán…). Bonus: model churn đơn giản + đánh giá.
6. Đầu ra: **dashboard** (Power BI / Tableau / Looker Studio / Metabase…) + notebook/SQL có thể chạy lại.

### 🧩 BA — "Vì sao, và sửa thế nào?"
1. Từ phát hiện của DA, làm **phân tích nguyên nhân gốc** (fishbone / 5 Whys) cho từng vấn đề lớn.
2. Vẽ **customer journey** từ đăng ký → onboarding → sử dụng → gia hạn/huỷ; vẽ **quy trình hiện tại (As-Is) và đề xuất (To-Be)** bằng BPMN cho ít nhất 1 quy trình (ví dụ onboarding, xử lý ticket, thu tiền).
3. Từ `lost_reason` trong pipeline và `category` của ticket, viết **yêu cầu sản phẩm**: 1 tài liệu BRD/PRD ngắn, ≥ 8 user story có acceptance criteria, ưu tiên bằng MoSCoW hoặc RICE.
4. Đề xuất **chính sách** cho các vấn đề không phải lỗi sản phẩm (giá, thanh toán, CSKH…) và đánh giá tác động.
5. Đầu ra: tài liệu phân tích + sơ đồ quy trình + backlog yêu cầu.

### 🤝 BD — "Tăng trưởng ở đâu?"
1. **Ước tính thị trường** (TAM/SAM/SOM) cho 1–2 phân khúc/khu vực tiềm năng nhất — tự tìm số liệu công khai, ghi rõ nguồn và giả định.
2. Phân tích **pipeline 2025**: win rate, chu kỳ chốt deal, giá trị theo nguồn và phân khúc; đánh giá hiệu quả **từng loại đối tác**.
3. Đề xuất **chiến lược kênh/đối tác**: mở rộng đối tác loại nào, mô hình hoa hồng ra sao, mục tiêu cụ thể.
4. Phân tích **2–3 đối thủ thực tế** trên thị trường POS Việt Nam (tính năng, giá, định vị) → GrowthOS định vị thế nào.
5. Đầu ra: go-to-market plan + mô hình tài chính đơn giản (doanh thu kỳ vọng, chi phí, payback).

---

## 4. Phần giao nhau (bắt buộc làm chung)

Đây là phần quan trọng nhất — nơi thể hiện khả năng phối hợp liên chức năng:

| Giao nhau | Câu hỏi cần trả lời cùng nhau |
|---|---|
| DA ∩ BA | Số liệu chỉ ra vấn đề nào, BA chứng minh nguyên nhân bằng quy trình nào? Giải pháp của BA được đo bằng KPI nào? |
| DA ∩ BD | Kênh/phân khúc nào BD muốn đẩy — số liệu retention & LTV có ủng hộ không? Dự báo doanh thu dựa trên giả định nào từ dữ liệu? |
| BA ∩ BD | Tính năng nào giúp thắng deal? Đáng làm không khi so với chi phí phát triển? Đối tác cần quy trình phối hợp thế nào? |
| **DA ∩ BA ∩ BD** | **GrowthOS nên chọn trọng tâm nào trong 3 hướng CEO đưa ra (hoặc kết hợp)? Phân bổ 1,5 tỷ ra sao? Đo thành công bằng gì?** |

### Sản phẩm cuối cùng
1. **Memo đề xuất 2 trang** gửi CEO (vấn đề → bằng chứng → đề xuất → rủi ro → KPI).
2. **Slide thuyết trình 10–12 trang**, trình bày trong 15 phút + 10 phút Q&A (nhờ mentor/bạn bè đóng vai CEO phản biện).
3. **Dashboard** theo dõi các KPI cam kết.
4. **Roadmap 2 quý**: việc gì, ai làm, khi nào, tốn bao nhiêu, kỳ vọng tác động bao nhiêu.
5. Repo này: code/SQL, tài liệu, sơ đồ — sắp xếp gọn để nhà tuyển dụng mở là hiểu.

---

## 5. Lịch gợi ý (4 tuần)

| Tuần | DA | BA | BD |
|---|---|---|---|
| 1 | Làm sạch dữ liệu, định nghĩa chỉ số, KPI tổng quan | Phỏng vấn giả định (đóng vai), vẽ journey As-Is | Nghiên cứu thị trường & đối thủ |
| 2 | Cohort, CAC/LTV, tìm bất thường | Root cause từng vấn đề | Phân tích pipeline & đối tác |
| 3 | Tín hiệu churn, dashboard | To-Be, BRD, backlog | GTM plan, mô hình tài chính |
| 4 | **Cả nhóm**: chốt trọng tâm, phân bổ ngân sách, memo, slide, tập thuyết trình | | |

Họp đồng bộ ngắn 2 lần/tuần — mỗi vai chia sẻ phát hiện để vai khác dùng ngay.

---

## 6. Tiêu chí tự đánh giá

| Tiêu chí | Trọng số | Câu hỏi tự kiểm tra |
|---|---|---|
| Đúng & sâu về số liệu | 25% | Chỉ số có định nghĩa rõ? Có phát hiện được hết các điểm bất thường không? Có tách được tương quan và nguyên nhân? |
| Chất lượng phân tích nghiệp vụ | 20% | Nguyên nhân gốc có thuyết phục? Yêu cầu có đo được, test được? |
| Tư duy thương mại | 20% | Đề xuất có tính tiền, tính ROI, tính payback? Giả định có hợp lý và ghi nguồn? |
| Liên kết giữa 3 vai | 20% | Đề xuất cuối có dùng bằng chứng của cả 3 vai, hay chỉ là 3 báo cáo đặt cạnh nhau? |
| Trình bày | 15% | CEO đọc memo 2 phút có hiểu nên làm gì không? |

---

## 7. Ghi vào CV thế nào

Viết theo dạng **hành động + công cụ + kết quả có số**, với số là do chính nhóm bạn tìm ra. Ví dụ khung (điền số của bạn vào):

- **DA**: "Phân tích ~28K bản ghi subscription của SaaS B2B bằng SQL/Python; xây cohort retention và CAC/LTV theo kênh, phát hiện [N] nguyên nhân khiến churn tăng [X]% trong [giai đoạn]; dựng dashboard [công cụ] theo dõi [N] KPI."
- **BA**: "Thực hiện root-cause analysis và mô hình hoá quy trình As-Is/To-Be (BPMN) cho [quy trình]; viết BRD với [N] user story ưu tiên theo RICE, ước tính giảm churn [X] điểm %."
- **BD**: "Ước tính TAM/SAM cho phân khúc [..]; phân tích pipeline [N] deal, đề xuất chiến lược đối tác [..] với dự báo +[X] MRR và payback [N] tháng."

Ghi rõ đây là **case study mô phỏng** (dữ liệu giả lập) — trung thực sẽ được đánh giá cao hơn, và bạn vẫn kể được trọn câu chuyện khi phỏng vấn.

---

## Cấu trúc repo gợi ý

```
data/
  raw/                 # dữ liệu gốc (không sửa)
  generate_data.py     # script sinh dữ liệu (đừng đọc!)
da/                    # SQL, notebook, dashboard
ba/                    # BRD, user story, sơ đồ BPMN
bd/                    # market sizing, GTM plan, mô hình tài chính
final/                 # memo, slide, roadmap
```
