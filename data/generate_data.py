"""
Sinh bộ dữ liệu giả lập cho case study GrowthOS.

!!! CẢNH BÁO: File này chứa "đáp án" (các quy luật được cài vào dữ liệu).
!!! Người làm case KHÔNG nên đọc file này. Chỉ cần chạy:
!!!     python3 data/generate_data.py
!!! Output: các file CSV trong data/raw/

Chỉ dùng thư viện chuẩn của Python, không cần cài thêm gì.
"""

import csv
import math
import os
import random
from datetime import date, timedelta

SEED = 2025
random.seed(SEED)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")

MONTHS = [date(2024 + (i // 12), i % 12 + 1, 1) for i in range(24)]  # 2024-01 .. 2025-12
PRICE_CHANGE = date(2025, 4, 1)
EWALLET_INCIDENT = (date(2025, 7, 1), date(2025, 9, 1))

SEGMENTS = {"Retail": 0.40, "F&B": 0.35, "Beauty": 0.15, "Pharmacy": 0.10}
CITIES = {
    "Hà Nội": 1, "TP.HCM": 1,
    "Đà Nẵng": 2, "Hải Phòng": 2, "Cần Thơ": 2,
    "Nha Trang": 3, "Huế": 3, "Vinh": 3, "Buôn Ma Thuột": 3, "Quy Nhơn": 3,
}
CITY_WEIGHTS = {"Hà Nội": 22, "TP.HCM": 28, "Đà Nẵng": 9, "Hải Phòng": 7, "Cần Thơ": 6,
                "Nha Trang": 6, "Huế": 5, "Vinh": 6, "Buôn Ma Thuột": 5, "Quy Nhơn": 6}
PAYMENT_METHODS = {"Bank transfer": 0.45, "E-wallet": 0.35, "Card": 0.20}

PARTNERS = [
    ("P01", "NH Phương Đông", "Bank", "TP.HCM", 0.15),
    ("P02", "NH Sông Hồng", "Bank", "Hà Nội", 0.15),
    ("P03", "Phân phối Minh Phát", "Distributor", "TP.HCM", 0.20),
    ("P04", "Phân phối Bắc Hà", "Distributor", "Hà Nội", 0.20),
    ("P05", "Kế toán An Tâm", "Accounting firm", "Đà Nẵng", 0.25),
    ("P06", "Kế toán Sao Việt", "Accounting firm", "Cần Thơ", 0.25),
]
PARTNER_CHURN_MULT = {"Bank": 0.5, "Distributor": 0.75, "Accounting firm": 0.65}


def pick(weights):
    keys = list(weights)
    return random.choices(keys, weights=[weights[k] for k in keys])[0]


def basic_price(m):
    return 249_000 if m >= PRICE_CHANGE else 199_000


def mrr_for(plan, stores, m):
    if plan == "Basic":
        return basic_price(m)
    if plan == "Pro":
        return 499_000 * stores
    return 1_200_000 * stores


def rand_day(m):
    nxt = MONTHS[MONTHS.index(m) + 1] if m != MONTHS[-1] else date(2026, 1, 1)
    return m + timedelta(days=random.randrange((nxt - m).days))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    customers, sub_rows, usage_rows, tickets, spend_rows = [], [], [], [], []
    active = []
    cid = tid = 0

    for mi, m in enumerate(MONTHS):
        # ---------- marketing spend & new signups ----------
        growth = 1 + mi * 0.03
        channel_signups = {
            "Ads": int(random.gauss(55, 6) * (1 + mi * 0.005)),      # ads gần như đi ngang
            "Organic": int(random.gauss(35, 5) * growth),
            "Sales": int(random.gauss(18, 3) * growth),
            "Partner": int(random.gauss(6, 2) + mi * 1.1),           # partner tăng dần
        }
        spend = {
            "Ads": int(180_000_000 * (1 + mi * 0.06) * random.uniform(0.95, 1.05)),
            "Organic": int(25_000_000 * random.uniform(0.9, 1.1)),   # content/SEO
            "Sales": int(90_000_000 * growth * random.uniform(0.95, 1.05)),
            "Partner": 0,  # hoa hồng tính ở dưới theo doanh thu thực
        }

        for channel, n in channel_signups.items():
            for _ in range(max(n, 0)):
                cid += 1
                seg = pick(SEGMENTS)
                city = pick(CITY_WEIGHTS)
                tier = CITIES[city]
                partner = random.choice(PARTNERS) if channel == "Partner" else None
                stores = 1
                r = random.random()
                if channel in ("Sales", "Partner") or seg == "Pharmacy":
                    stores = 1 if r < 0.45 else (random.randint(2, 4) if r < 0.85 else random.randint(5, 12))
                else:
                    stores = 1 if r < 0.75 else (random.randint(2, 4) if r < 0.95 else random.randint(5, 8))
                plan = "Basic" if stores == 1 and random.random() < 0.8 else ("Enterprise" if stores >= 5 else "Pro")
                onboard_p = {1: 0.78, 2: 0.62, 3: 0.48}[tier]
                if channel in ("Sales", "Partner"):
                    onboard_p += 0.12
                c = {
                    "customer_id": f"C{cid:05d}",
                    "signup_date": rand_day(m).isoformat(),
                    "segment": seg,
                    "city": city,
                    "city_tier": tier,
                    "store_count_at_signup": stores,
                    "acquisition_channel": channel,
                    "partner_id": partner[0] if partner else "",
                    "onboarding_completed": int(random.random() < onboard_p),
                    "payment_method": pick(PAYMENT_METHODS),
                    # trạng thái nội bộ
                    "_plan": plan, "_stores": stores, "_partner_type": partner[2] if partner else None,
                    "_partner_comm": partner[4] if partner else 0, "_bad_support_until": -1,
                    "_start": mi,
                }
                customers.append(c)
                active.append(c)

        # ---------- simulate active customers this month ----------
        still_active, partner_commission = [], 0
        for c in active:
            hazard = 0.022
            hazard *= {"Retail": 1.0, "F&B": 1.8, "Beauty": 1.1, "Pharmacy": 0.45}[c["segment"]]
            hazard *= {1: 1.0, 2: 1.3, 3: 1.6}[c["city_tier"]]
            if not c["onboarding_completed"]:
                hazard *= 2.2
            hazard *= {"Ads": 1.3, "Organic": 1.0, "Sales": 0.85, "Partner": 1.0}[c["acquisition_channel"]]
            if c["_partner_type"]:
                hazard *= PARTNER_CHURN_MULT[c["_partner_type"]]
            if c["_plan"] == "Basic" and m >= PRICE_CHANGE and c["_stores"] == 1:
                months_since = MONTHS.index(m) - MONTHS.index(PRICE_CHANGE)
                hazard *= 2.3 if months_since < 3 else 1.3
            if c["_plan"] == "Enterprise":
                hazard *= 0.5
            if c["_bad_support_until"] >= mi:
                hazard *= 1.9
            if mi == c["_start"]:
                hazard *= 0.3  # tháng đầu ít khi huỷ ngay

            # support tickets
            if random.random() < (0.18 if not c["onboarding_completed"] else 0.10):
                tid += 1
                cat = random.choices(
                    ["Inventory sync", "Billing", "Printer/Hardware", "How-to", "E-invoice"],
                    weights=[25, 15, 20, 30, 10])[0]
                base_res = {"Inventory sync": 30, "Billing": 10, "Printer/Hardware": 20, "How-to": 4, "E-invoice": 26}[cat]
                if cat == "Inventory sync" and c["city_tier"] == 3:
                    base_res *= 1.8
                res = max(0.5, random.expovariate(1 / base_res))
                csat = max(1, min(5, round(random.gauss(4.4 - res / 30, 0.7))))
                tickets.append({
                    "ticket_id": f"T{tid:06d}", "customer_id": c["customer_id"],
                    "created_date": rand_day(m).isoformat(), "category": cat,
                    "resolution_hours": round(res, 1), "csat": csat,
                })
                if cat == "Inventory sync" and res > 48:
                    c["_bad_support_until"] = mi + 3

            # payment
            fail_p = 0.02
            if c["payment_method"] == "E-wallet" and EWALLET_INCIDENT[0] <= m <= EWALLET_INCIDENT[1]:
                fail_p = 0.13
            payment_failed = random.random() < fail_p

            churned = random.random() < min(hazard, 0.9) or (payment_failed and random.random() < 0.35)

            # store growth & upgrades
            if not churned:
                if random.random() < (0.03 if c["segment"] == "Pharmacy" else 0.008):
                    c["_stores"] += 1
                if c["_plan"] == "Basic" and random.random() < (0.05 if c["_stores"] >= 2 else 0.012):
                    c["_plan"] = "Pro"
                elif c["_plan"] == "Pro" and c["_stores"] >= 5 and random.random() < 0.06:
                    c["_plan"] = "Enterprise"

            mrr = mrr_for(c["_plan"], c["_stores"], m)
            sub_rows.append({
                "customer_id": c["customer_id"], "month": m.isoformat(), "plan": c["_plan"],
                "store_count": c["_stores"], "mrr_vnd": mrr,
                "payment_method": c["payment_method"], "payment_failed": int(payment_failed),
                "status": "churned" if churned else "active",
            })

            # usage: rủi ro càng cao thì dùng càng ít
            risk = math.log(max(hazard, 0.001) / 0.022)
            active_days = int(max(0, min(30, random.gauss(23 - 4.5 * risk, 4))))
            tx_per_day = random.uniform(15, 60) * c["_stores"] * (1.5 if c["segment"] == "F&B" else 1)
            usage_rows.append({
                "customer_id": c["customer_id"], "month": m.isoformat(),
                "active_days": active_days,
                "transactions": int(active_days * tx_per_day),
                "features_used": max(1, min(12, int(random.gauss(6 - risk, 2)))),
                "staff_accounts": max(1, int(random.gauss(2.5 * c["_stores"], 1))),
            })

            if c["_partner_comm"] and mi - c["_start"] < 12:
                partner_commission += mrr * c["_partner_comm"]
            if not churned:
                still_active.append(c)
        active = still_active

        spend["Partner"] = int(partner_commission + 15_000_000)  # + chi phí quản lý đối tác
        for ch, v in spend.items():
            spend_rows.append({"month": m.isoformat(), "channel": ch, "spend_vnd": v})

    # ---------- BD pipeline: deal chuỗi nhiều cửa hàng, 2025 ----------
    leads = []
    lid = 0
    source_w = {"Partner - Bank": 15, "Partner - Distributor": 15, "Event": 15, "Outbound": 30, "Inbound": 25}
    for m in MONTHS[12:]:
        for _ in range(random.randint(45, 65)):
            lid += 1
            src = pick(source_w)
            seg = pick({"Retail": 40, "F&B": 30, "Beauty": 15, "Pharmacy": 15})
            stores = random.randint(3, 40)
            win = {"Partner - Bank": 0.32, "Partner - Distributor": 0.24, "Event": 0.15,
                   "Outbound": 0.08, "Inbound": 0.18}[src]
            win *= {"Retail": 1.0, "F&B": 0.8, "Beauty": 0.9, "Pharmacy": 1.7}[seg]
            created = rand_day(m)
            r = random.random()
            stage_reached = random.choices(["New", "Qualified", "Demo", "Proposal"], weights=[15, 25, 30, 30])[0]
            if r < win:
                stage, lost_reason = "Won", ""
            elif created > date(2025, 11, 1) and random.random() < 0.6:
                stage, lost_reason = stage_reached, ""  # còn mở
            else:
                stage = "Lost"
                lost_reason = random.choices(
                    ["Thiếu hoá đơn điện tử", "Giá cao", "Chọn đối thủ", "Không phản hồi", "Thiếu tích hợp kế toán"],
                    weights=[34 if seg != "F&B" else 20, 18, 16, 22, 10 if seg != "Pharmacy" else 25])[0]
            closed = (created + timedelta(days=int(random.gauss(
                {"Partner - Bank": 28, "Partner - Distributor": 35}.get(src, 50), 12)))) if stage in ("Won", "Lost") else None
            leads.append({
                "lead_id": f"L{lid:05d}", "created_date": created.isoformat(), "source": src,
                "segment": seg, "city": pick(CITY_WEIGHTS), "store_count": stores,
                "stage": stage, "est_mrr_vnd": stores * random.choice([499_000, 1_200_000]),
                "closed_date": closed.isoformat() if closed and closed <= date(2025, 12, 31) else "",
                "lost_reason": lost_reason,
                "owner": random.choice(["Huy", "Trang", "Nam", "Linh", "Quân"]),
            })

    # ---------- write ----------
    def write(name, rows, fields=None):
        fields = fields or [k for k in rows[0] if not k.startswith("_")]
        with open(os.path.join(OUT_DIR, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"  {name}: {len(rows):,} dòng")

    print(f"Đang ghi vào {OUT_DIR}")
    write("customers.csv", customers)
    write("subscriptions_monthly.csv", sub_rows)
    write("usage_monthly.csv", usage_rows)
    write("support_tickets.csv", tickets)
    write("marketing_spend.csv", spend_rows)
    write("leads.csv", leads)
    write("partners.csv", [dict(zip(["partner_id", "name", "type", "city", "commission_rate"], p)) for p in PARTNERS])


if __name__ == "__main__":
    main()
