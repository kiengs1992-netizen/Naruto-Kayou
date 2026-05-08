import io
import re
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Naruto Kayou Price Checker", page_icon="🃏", layout="wide")

RARITIES = ["", "R", "SR", "SSR", "UR", "OR", "AR", "BP", "SP", "MR", "CR", "XR", "QR", "NR", "SE", "PR"]
SERIES = [
    "", "T1W1", "T1W2", "T1W3", "T1W4", "T2W1", "T2W2", "T2W3", "T2W4",
    "T3W1", "T3W2", "T3W3", "T3W4", "T4W1", "T4W2", "T4W3", "T4W4", "T4W5", "T4W6", "T4W7",
    "Heaven Scroll", "Earth Scroll", "Jin Chapter", "Promo", "Event", "PR"
]

CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.5rem;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#ffffff 0%,#f1f5f9 100%); border-right: 1px solid #e2e8f0;}
[data-testid="stSidebar"] * {color: #0f172a !important;}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] div[data-baseweb="select"] > div {background-color: #ffffff !important; color: #0f172a !important; border-color: #cbd5e1 !important;}
[data-testid="stSidebar"] input::placeholder {color: #64748b !important; opacity: 1 !important;}
.hero {padding: 24px; border-radius: 24px; background: linear-gradient(135deg,#1d4ed8 0%,#7c3aed 60%,#f97316 100%); color: white; box-shadow: 0 12px 32px rgba(15,23,42,.15);}
.hero h1 {margin:0; font-size: 34px; color:white;}
.hero p {margin-top:8px; color:#e0e7ff; font-size:16px;}
.card {background:white; border:1px solid #e2e8f0; border-radius:20px; padding:18px; box-shadow:0 6px 20px rgba(15,23,42,.06);}
.small-muted {color:#64748b; font-size:13px;}
.price {font-size:24px; font-weight:700; color:#0f172a;}
a {text-decoration:none;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def build_query(series, character, rarity, card_no, extra):
    parts = ["Naruto Kayou"]
    for x in [series, character, rarity, card_no, extra]:
        if x and str(x).strip():
            parts.append(str(x).strip())
    return " ".join(parts)


def ebay_search_url(query):
    return "https://www.ebay.com/sch/i.html?_nkw=" + quote_plus(query)


def ebay_sold_url(query):
    return "https://www.ebay.com/sch/i.html?_nkw=" + quote_plus(query) + "&LH_Sold=1&LH_Complete=1"


def point130_url(query):
    return "https://130point.com/sales/?search=" + quote_plus(query)


def clean_price(value):
    if pd.isna(value):
        return None
    text = str(value)
    nums = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
    return float(nums[0]) if nums else None


def normalize_csv(df, fx_rate):
    df = df.copy()
    lower_map = {c.lower().strip(): c for c in df.columns}
    title_col = lower_map.get("title") or lower_map.get("name") or lower_map.get("item")
    price_col = lower_map.get("price") or lower_map.get("sold_price") or lower_map.get("usd")
    image_col = lower_map.get("image_url") or lower_map.get("image")
    url_col = lower_map.get("url") or lower_map.get("link")
    if not title_col or not price_col:
        return pd.DataFrame()
    out = pd.DataFrame()
    out["title"] = df[title_col].astype(str)
    out["price_usd"] = df[price_col].apply(clean_price)
    out["price_thb"] = out["price_usd"] * fx_rate
    out["image_url"] = df[image_col].astype(str) if image_col else ""
    out["url"] = df[url_col].astype(str) if url_col else ""
    return out.dropna(subset=["price_usd"])


def fetch_ebay_api(query, token, limit, fx_rate):
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}
    params = {"q": query, "limit": min(limit, 200)}
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    items = r.json().get("itemSummaries", [])
    rows = []
    for it in items:
        price = it.get("price", {}).get("value")
        try:
            price_usd = float(price)
        except Exception:
            continue
        rows.append({
            "title": it.get("title", ""),
            "price_usd": price_usd,
            "price_thb": price_usd * fx_rate,
            "image_url": it.get("image", {}).get("imageUrl", ""),
            "url": it.get("itemWebUrl", ""),
        })
    return pd.DataFrame(rows)

with st.sidebar:
    st.header("🔎 ค้นหาราคา")
    series = st.selectbox("ชื่อรุ่น / Wave", SERIES, placeholder="เช่น T4W7, Jin Chapter")
    character = st.text_input("ชื่อตัวละคร", placeholder="Naruto / Sasuke / Itachi")
    rarity = st.selectbox("Rarity", RARITIES, placeholder="AR / BP / SP")
    card_no = st.text_input("เลขการ์ด", placeholder="เช่น NR-001, AR-12")
    extra = st.text_input("Keyword เพิ่มเติม", placeholder="EN / graded / PSA")
    fx_rate = st.number_input("USD → THB", min_value=1.0, value=36.0, step=0.25)
    limit = st.slider("จำนวนรายการสูงสุด", 10, 200, 50)
    source = st.radio("แหล่งข้อมูล", ["Search Link Only", "Manual Sold CSV", "eBay Active API"])

query = build_query(series, character, rarity, card_no, extra)

st.markdown(f"""
<div class="hero">
  <h1>🃏 Naruto Kayou Price Checker</h1>
  <p>ค้นราคา Kayou แบบใช้งานง่าย พร้อมลิงก์ eBay Sold, 130point, CSV Sold Price และรูปการ์ดจาก image_url / eBay API</p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.markdown(f"### Keyword ที่ใช้ค้นหา: `{query}`")

c1, c2, c3 = st.columns(3)
c1.link_button("เปิด eBay Active", ebay_search_url(query), use_container_width=True)
c2.link_button("เปิด eBay Sold", ebay_sold_url(query), use_container_width=True)
c3.link_button("เปิด 130point", point130_url(query), use_container_width=True)

results = pd.DataFrame()
if source == "Manual Sold CSV":
    file = st.file_uploader("Upload CSV ที่มีคอลัมน์ title, price และถ้ามี image_url, url", type=["csv"])
    if file:
        raw = pd.read_csv(file)
        results = normalize_csv(raw, fx_rate)
elif source == "eBay Active API":
    token = st.text_input("eBay OAuth Token", type="password")
    if st.button("ดึงข้อมูลจาก eBay API", type="primary"):
        if not token:
            st.warning("กรุณาใส่ eBay OAuth Token")
        else:
            try:
                results = fetch_ebay_api(query, token, limit, fx_rate)
                st.session_state["results"] = results
            except Exception as e:
                st.error(f"ดึงข้อมูลไม่สำเร็จ: {e}")
    results = st.session_state.get("results", results)

if not results.empty:
    t1, t2, t3, t4 = st.tabs(["📊 Summary", "🧾 รายการราคา", "🖼️ รูปการ์ด", "⬇️ Export"])
    with t1:
        a, b, c, d = st.columns(4)
        a.metric("จำนวนรายการ", f"{len(results):,.0f}")
        b.metric("ต่ำสุด THB", f"{results['price_thb'].min():,.0f}")
        c.metric("กลาง THB", f"{results['price_thb'].median():,.0f}")
        d.metric("สูงสุด THB", f"{results['price_thb'].max():,.0f}")
        st.bar_chart(results.sort_values("price_thb").tail(20).set_index("title")["price_thb"])
    with t2:
        st.dataframe(results, use_container_width=True, hide_index=True)
    with t3:
        cols = st.columns(4)
        for idx, row in results.iterrows():
            with cols[idx % 4]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                img = str(row.get("image_url", ""))
                if img.startswith("http"):
                    st.image(img, use_container_width=True)
                st.markdown(f"**{row.get('title','')}**")
                st.markdown(f"<div class='price'>฿{row.get('price_thb',0):,.0f}</div>", unsafe_allow_html=True)
                url = str(row.get("url", ""))
                if url.startswith("http"):
                    st.link_button("เปิดรายการ", url, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
    with t4:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            results.to_excel(writer, index=False, sheet_name="Price Results")
        st.download_button("Download Excel", output.getvalue(), file_name="naruto_kayou_price_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("เลือกแหล่งข้อมูลด้านซ้าย ถ้าใช้ Search Link Only ให้กดปุ่มเปิด eBay / 130point ด้านบน")
