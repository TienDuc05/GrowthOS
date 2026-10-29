# Olist E-Commerce — Case study DA × BA × BD

> Case study dựa trên **dữ liệu thật, công khai** của Olist (sàn thương mại điện tử Brazil, 2016–2018), làm theo nhóm 3 vai: **Data Analyst (DA)**, **Business Analyst (BA)**, **Business Development (BD)**.
> Đề chỉ cho bối cảnh, dữ liệu và câu hỏi. Đáp án là của nhóm bạn.

---

## 1. Bối cảnh

**Olist** là công ty Brazil giúp người bán nhỏ (seller) đưa sản phẩm lên các sàn thương mại điện tử lớn thông qua một "cửa hàng" chung.
Olist kiếm tiền từ seller, nên có hai bài toán song song:
- **Phía người mua:** đơn hàng phải giao đúng hẹn, khách hài lòng và quay lại mua.
- **Phía người bán:** đội sales phải tuyển được seller tốt, và seller sau khi vào phải bán được hàng.

### Email của Head of Growth gửi nhóm bạn (giả định, đầu tháng 09/2018)

> Chào cả nhóm,
>
> Số đơn tăng mạnh từ 2017 nhưng ban lãnh đạo lo ba chuyện:
> trải nghiệm giao hàng và đánh giá của khách, khả năng giữ chân người mua, và hiệu quả của đội tuyển seller (tốn công nhưng không rõ seller nào thực sự mang lại doanh số).
>
> Cho 2 quý tới, công ty cần chọn **một trọng tâm** để dồn nguồn lực:
> 1. Cải thiện vận hành giao hàng & trải nghiệm khách,
> 2. Tăng mua lại / giá trị vòng đời người mua,
> 3. Tối ưu tuyển seller (đúng phân khúc, đúng kênh).
>
> Anh cần các em trả lời: **chuyện gì đang xảy ra, vì sao, và Olist nên dồn lực vào đâu**, kèm số liệu, giải pháp và kế hoạch triển khai.
> Ngân sách bổ sung tối đa: **R$ 2 triệu** cho 2 quý.

---

## 2. Dữ liệu

Hai bộ dữ liệu gốc trên Kaggle, **nối được với nhau thật** qua `seller_id`:

| Bộ | Nội dung | Link |
|---|---|---|
| Olist Brazilian E-Commerce | ~100 nghìn đơn hàng 2016–2018, 9 bảng | https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce |
| Olist Marketing Funnel | ~8 nghìn lead seller (MQL) và các deal đã chốt | https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist |

### Bảng chính

| Schema.bảng | Mỗi dòng là | Khoá nối |
|---|---|---|
| `olist_ecommerce.orders` | 1 đơn hàng, kèm các mốc thời gian: mua, duyệt, giao cho vận chuyển, giao tới khách, ngày dự kiến | `order_id`, `customer_id` |
| `olist_ecommerce.order_items` | 1 sản phẩm trong đơn (giá, phí ship) | `order_id`, `product_id`, `seller_id` |
| `olist_ecommerce.order_payments` | 1 lần thanh toán (loại, số kỳ trả góp) | `order_id` |
| `olist_ecommerce.order_reviews` | 1 đánh giá (điểm 1–5, bình luận tiếng Bồ Đào Nha) | `order_id` |
| `olist_ecommerce.customers` | 1 `customer_id` theo đơn; người mua thật là `customer_unique_id` | `customer_id` |
| `olist_ecommerce.sellers` | 1 seller (thành phố, bang) | `seller_id` |
| `olist_ecommerce.products` | 1 sản phẩm (danh mục, kích thước, cân nặng) | `product_id` |
| `olist_ecommerce.geolocation` | toạ độ theo mã bưu chính | `zip_code_prefix` |
| `olist_ecommerce.category_translation` | tên danh mục Bồ Đào Nha → tiếng Anh | `product_category_name` |
| `olist_marketing.marketing_qualified_leads` | 1 lead seller (ngày liên hệ, kênh `origin`) | `mql_id` |
| `olist_marketing.closed_deals` | 1 deal đã chốt (phân khúc, loại lead, quy mô…) | `mql_id`, `seller_id` |
| `marts.olist_seller_growth` | (view dựng sẵn) seller đã chốt + kênh marketing + doanh số sau khi vào sàn | `seller_id` |

> Lưu ý khi phân tích: `customer_id` **không** phải người mua duy nhất; dữ liệu marketing chỉ phủ khoảng 06/2017–05/2018; hai đầu chuỗi thời gian đơn hàng có rất ít dữ liệu. Tự kiểm tra và ghi rõ cách xử lý của nhóm.

### Cách lấy dữ liệu

Cần Python 3.10+ và tài khoản Kaggle (đã cấu hình API token cho `kagglehub`). Chạy ở thư mục gốc của repo:

```bash
python -m pip install -r requirements.txt
```

```bash
python scripts/download_data.py
```

```bash
python scripts/build_database.py
```

Windows: nhấp đúp `RUN_WINDOWS.bat`.
Không dùng được Kaggle API thì tải ZIP thủ công từ 2 link trên, giải nén CSV vào `data/raw/olist_ecommerce/` và `data/raw/olist_marketing/`, rồi chạy `build_database.py`.

Kết quả: `data/processed/olist.duckdb` — truy vấn bằng DuckDB/Python, hoặc xuất bảng sang CSV cho Excel/Power BI. Ví dụ truy vấn: `sql/analysis_queries.sql`.

---

## 3. Nhiệm vụ theo vai

### 📊 DA — "Chuyện gì đang xảy ra?"
1. Bộ **chỉ số tổng quan** theo tháng: số đơn, GMV, AOV, số người mua, số seller hoạt động; theo bang và danh mục.
2. **Giao hàng:** thời gian giao thực tế so với ngày hứa, tỉ lệ giao trễ; trễ ở khâu nào (duyệt đơn, seller gửi hàng, vận chuyển); khác biệt theo vùng, danh mục, seller.
3. **Đánh giá:** điểm review liên quan thế nào đến giao hàng, phí ship, danh mục, seller?
4. **Giữ chân người mua:** tỉ lệ mua lại, cohort retention, phân khúc RFM — dùng đúng `customer_unique_id`.
5. **Seller:** phân bố doanh số giữa các seller; seller nào kéo điểm review xuống.
6. Đầu ra: **dashboard** + notebook/SQL chạy lại được.

### 🧩 BA — "Vì sao, và sửa thế nào?"
1. Vẽ **quy trình đơn hàng As-Is** (đặt → duyệt → seller đóng gói → giao vận chuyển → nhận hàng → đánh giá) bằng BPMN, gắn số liệu thời gian của DA vào từng bước.
2. **Root cause** cho vấn đề trải nghiệm lớn nhất (fishbone / 5 Whys), có bằng chứng số liệu.
3. **Đọc bình luận review** (dịch hoặc phân loại chủ đề) để biết khách phàn nàn điều gì — kết hợp phân tích định tính với số liệu.
4. Thiết kế **To-Be** và viết yêu cầu cho 1–2 giải pháp (ví dụ: bảng điểm seller, cách ước tính ngày giao, cảnh báo đơn có nguy cơ trễ): BRD ngắn + ≥ 8 user story có acceptance criteria, ưu tiên bằng RICE/MoSCoW.
5. Đề xuất **KPI và SLA** cho seller và vận chuyển.

### 🤝 BD — "Tăng trưởng ở đâu?"
1. **Phễu tuyển seller:** MQL → deal theo kênh `origin`, thời gian chốt, phân khúc, loại lead.
2. **Chất lượng seller sau khi vào sàn** (dùng `marts.olist_seller_growth`): kênh/phân khúc nào mang lại seller bán được hàng, kênh nào chỉ mang lại số lượng.
3. **Cơ hội danh mục & vùng:** danh mục/bang nào có cầu lớn nhưng thiếu seller hoặc trải nghiệm kém?
4. **Chiến lược tuyển seller** cho 2 quý: nhắm phân khúc nào, kênh nào, chỉ tiêu và chi phí.
5. Tìm hiểu bối cảnh thị trường TMĐT Brazil và 2–3 đối thủ/mô hình tương tự — ghi nguồn.
6. Đầu ra: kế hoạch go-to-market cho seller + mô hình tài chính đơn giản (chi phí, doanh thu kỳ vọng, payback).

---

## 4. Phần giao nhau (bắt buộc làm chung)

| Giao nhau | Câu hỏi |
|---|---|
| DA ∩ BA | Số liệu chỉ ra điểm nghẽn ở khâu nào; quy trình nào giải thích được nó? Giải pháp đo bằng KPI nào? |
| DA ∩ BD | Phân khúc/kênh BD muốn đẩy có dữ liệu doanh số và review ủng hộ không? |
| BA ∩ BD | Tiêu chuẩn chất lượng seller (BA) nên đưa vào quy trình tuyển seller (BD) thế nào? |
| **DA ∩ BA ∩ BD** | **Chọn trọng tâm nào trong 3 hướng (hoặc kết hợp)? Phân bổ R$ 2 triệu ra sao? Đo thành công bằng gì?** |

### Sản phẩm cuối
1. **Memo 2 trang** gửi Head of Growth (vấn đề → bằng chứng → đề xuất → rủi ro → KPI).
2. **Slide 10–12 trang**, thuyết trình 15 phút + 10 phút Q&A.
3. **Dashboard** theo dõi KPI cam kết.
4. **Roadmap 2 quý**: việc gì, ai làm, khi nào, chi phí, tác động kỳ vọng.

---

## 5. Lịch gợi ý (4 tuần)

| Tuần | DA | BA | BD |
|---|---|---|---|
| 1 | Tải & làm sạch dữ liệu, định nghĩa chỉ số, KPI tổng quan | Quy trình đơn hàng As-Is | Phễu tuyển seller |
| 2 | Giao hàng & review, retention/RFM | Root cause, phân tích bình luận | Chất lượng seller theo kênh, cơ hội danh mục/vùng |
| 3 | Phân tích seller, dashboard | To-Be, BRD, user story, KPI/SLA | GTM seller, mô hình tài chính |
| 4 | **Cả nhóm**: chốt trọng tâm, ngân sách, memo, slide, tập thuyết trình | | |

---

## 6. Tiêu chí tự đánh giá

| Tiêu chí | Trọng số |
|---|---|
| Đúng & sâu về số liệu (xử lý đúng các bẫy dữ liệu, không nhân bản dòng khi join) | 25% |
| Chất lượng phân tích nghiệp vụ | 20% |
| Tư duy thương mại (ROI, payback, giả định có nguồn) | 20% |
| Liên kết giữa 3 vai | 20% |
| Trình bày | 15% |

---

## 7. Ghi vào CV

Đây là **dữ liệu thật** (đơn hàng ẩn danh của Olist), nên có thể ghi "phân tích ~100K đơn hàng thực tế của sàn TMĐT Olist (Brazil)". Ví dụ khung (điền số của nhóm bạn):

- **DA**: "Phân tích ~100K đơn hàng của Olist bằng SQL/Python; xác định [yếu tố] làm điểm review giảm [X]; xây cohort/RFM và dashboard [công cụ] theo dõi [N] KPI."
- **BA**: "Mô hình hoá quy trình fulfillment As-Is/To-Be (BPMN), phân tích root cause giao trễ; viết BRD với [N] user story cho [giải pháp]."
- **BD**: "Phân tích phễu ~8K lead seller; đề xuất chiến lược tuyển seller theo [kênh/phân khúc] với dự báo +[X] GMV, payback [N] tháng."

---

## 8. Nguồn & giấy phép

- Olist, *Brazilian E-Commerce Public Dataset by Olist* và *Marketing Funnel by Olist*, Kaggle — giấy phép **CC BY-NC-SA 4.0**: ghi nguồn, phi thương mại, chia sẻ cùng giấy phép. Kiểm tra lại trên trang gốc trước khi dùng.
- Dữ liệu gốc **không được commit** vào repo (xem `.gitignore`); mỗi người tự tải bằng script.

## Cấu trúc

```text
GrowthOS/
├── README.md              # đề bài (file này)
├── requirements.txt
├── RUN_WINDOWS.bat
├── scripts/
│   ├── download_data.py   # tải 2 bộ dữ liệu Olist từ Kaggle
│   └── build_database.py  # import vào data/processed/olist.duckdb + view marts.olist_seller_growth
├── sql/analysis_queries.sql
├── docs/data_sources.csv
└── data/
    ├── raw/               # CSV tải về (không commit)
    └── processed/         # DuckDB (không commit)
```
