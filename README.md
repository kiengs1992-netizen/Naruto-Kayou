# Naruto Kayou Price Checker

Web app สำหรับเช็คราคาการ์ด Naruto Kayou ทุกรุ่นแบบค้นสด ไม่ Fix ราคาค้างในโปรแกรม

## Feature

- เลือกรุ่น Kayou Chinese Tier/Wave และ English mapping เช่น Heaven Scroll, Earth Scroll, Jin Chapter
- ค้นด้วยตัวละคร, Rarity, เลขการ์ด, keyword เพิ่มเติม
- เปิดลิงก์ eBay Active / eBay Sold ได้ทันที
- ดึง Active Listing ด้วย eBay Browse API ถ้ามี OAuth Token
- อัปโหลด Sold Price CSV จาก eBay sold / 130point / record เอง แล้วคำนวณราคาไทย
- ตัดราคาหลุดตลาดด้วย IQR
- Export Excel Report

## วิธีรันบน Windows

```bat
cd C:\path\to\naruto_kayou_price_checker
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

ถ้าเครื่องใช้คำสั่ง `py` ได้:

```bat
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

## วิธีรันบน Mac

```bash
cd /path/to/naruto_kayou_price_checker
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## การใช้ eBay API

1. สมัคร eBay Developer Account
2. สร้าง App แล้วขอ OAuth Application Token สำหรับ Buy Browse API
3. Copy `.streamlit/secrets.toml.example` เป็น `.streamlit/secrets.toml`
4. ใส่ Token:

```toml
EBAY_OAUTH_TOKEN = "your_token"
```

> หมายเหตุ: eBay Browse API เหมาะกับ Active Listing ส่วน Sold/Completed Listing แนะนำใช้ CSV จาก eBay sold/130point หรือ API ภายนอกที่มีสิทธิ์ถูกต้อง

## CSV Format สำหรับ Sold Price

ขั้นต่ำ:

```csv
title,price,currency
Naruto Kayou Jin Chapter Sasuke AR,18,USD
```

แนะนำ:

```csv
title,price,shipping,currency,sold_date,condition,item_url,seller
Naruto Kayou Jin Chapter Sasuke AR,18,3,USD,2026-05-01,Ungraded,https://...,sellername
```

## หมายเหตุสำคัญ

- ราคาการ์ด Kayou บางใบตลาดเล็กมาก ต้องใช้ Sold Price หลายแหล่งประกอบ
- Active Listing คือราคาตั้งขาย ไม่ใช่ราคาขายจริง
- ควรเทียบภาษา Chinese/English, รุ่นกล่อง, rarity, เลขการ์ด, สภาพ และเกรดก่อนสรุปราคา
