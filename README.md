import base64
from io import BytesIO
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Naruto Kayou Price Checker",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded",
)

KAYOU_WAVES = [
    "T1W1", "T1W2", "T1W3", "T1W4", "T2W1", "T2W2", "T2W3", "T2W4",
    "T3W1", "T3W2", "T3W3", "T3W4", "T4W1", "T4W2", "T4W3", "T4W4", "T4W5", "T4W6", "T4W7",
    "Jin Chapter", "Heaven Scroll", "Earth Scroll", "Promo / Event / PR", "Other"
]
KAYOU_RARITIES = ["", "R", "SR", "SSR", "UR", "OR", "AR", "BP", "SP", "MR", "CR", "XR", "QR", "NR", "PR", "HR", "SLR", "SE", "CP", "Other"]

CSS = """
<style>
    .stApp { background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%); }
    section[data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e5e7eb; }
    section[data-testid="stSidebar"] * { color: #0f172a !important; }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] input::placeholder { color: #64748b !important; opacity: 1 !important; }
    .hero {
        border-radius: 22px;
        padding: 30px 34px;
        color: white;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 55%, #f97316 100%);
        box-shadow: 0 18px 40px rgba(37, 99, 235, 0.25);
        margin-bottom: 24px;
    }
    .hero h1 { font-size: 34px; margin-bottom: 8px; }
    .hero p { font-size: 16px; opacity: 0.95; margin: 0; }
    .info-box {
        padding: 14px 16px;
        border-radius: 14px;
        background: #dbeafe;
        color: #1e3a8a;
        border: 1px solid #bfdbfe;
        margin-bottom: 18px;
    }
    .card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 14px;
        min-height: 420px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 14px 32px rgba(15, 23, 42, 0.12); }
    .card-img {
        width: 100%;
        height: 230px;
        object-fit: contain;
        border-radius: 14px;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
    }
    .card-title { font-weight: 700; font-size: 14px; color: #0f172a; margin-top: 10px; min-height: 54px; }
    .price { font-size: 18px; font-weight: 800; color: #2563eb; }
    .price-thb { font-size: 14px; color: #334155; }
    .muted { color: #64748b; font-size: 13px; }
    .pill { display:inline-block; padding:4px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:12px; margin-right:4px; }
    div[data-testid="stMetric"] { background: white; padding: 16px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 8px 20px rgba(15,23,42,.05); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def build_query(wave: str, character: str, rarity: str, card_no: str, extra: str) -> str:
    parts = ["Naruto Kayou", wave, character, rarity, card_no, extra]
    return " ".join([p.strip() for p in parts if p and p.strip()])


def market_links(query: str):
    q = quote_plus(query)
    return {
        "eBay Active": f"https://www.ebay.com/sch/i.html?_nkw={q}",
        "eBay Sold": f"https://www.ebay.com/sch/i.html?_nkw={q}&LH_Sold=1&LH_Complete=1",
        "130point": f"https://130point.com/sales/?search={q}",
    }


def search_ebay_items(query: str, token: str, limit: int = 24) -> pd.DataFrame:
    if not token:
        return pd.DataFrame()

    endpoint = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    params = {
        "q": query,
        "limit": min(int(limit), 200),
        "filter": "buyingOptions:{FIXED_PRICE|AUCTION}",
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=25)
        response.raise_for_status()
        payload = response.json()
        rows = []
        for item in payload.get("itemSummaries", []):
            price_obj = item.get("price") or {}
            image_obj = item.get("image") or {}
            rows.append({
                "title": item.get("title", ""),
                "price": pd.to_numeric(price_obj.get("value", 0), errors="coerce"),
                "currency": price_obj.get("currency", ""),
                "image_url": image_obj.get("imageUrl", ""),
                "item_url": item.get("itemWebUrl", ""),
                "condition": item.get("condition", ""),
                "seller": (item.get("seller") or {}).get("username", ""),
                "source": "eBay Active API",
            })
        return pd.DataFrame(rows)
    except Exception as exc:
        st.error(f"ดึงข้อมูลจาก eBay API ไม่สำเร็จ: {exc}")
        return pd.DataFrame()


def normalize_csv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    rename_map = {
        "name": "title", "card": "title", "url": "item_url", "link": "item_url",
        "image": "image_url", "img": "image_url", "amount": "price"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    for col in ["title", "price", "currency", "image_url", "item_url", "condition"]:
        if col not in df.columns:
            df[col] = "" if col != "price" else 0
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    if "source" not in df.columns:
        df["source"] = "Manual CSV"
    return df


def clean_df(df: pd.DataFrame, only_with_image: bool, sort_by: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if only_with_image and "image_url" in out.columns:
        out = out[out["image_url"].astype(str).str.len() > 5]
    if sort_by == "ราคาต่ำ → สูง":
        out = out.sort_values("price", ascending=True)
    elif sort_by == "ราคาสูง → ต่ำ":
        out = out.sort_values("price", ascending=False)
    return out.reset_index(drop=True)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Price Results")
    return output.getvalue()


def show_cards(df: pd.DataFrame, usd_to_thb: float):
    if df.empty:
        st.markdown(
            """
            <div class='info-box'>
            ยังไม่มีรูปการ์ดในหน้านี้<br>
            วิธีให้รูปขึ้น: เลือก <b>eBay Active API</b> แล้วใส่ Bearer Token หรือเลือก <b>Manual Sold CSV</b> ที่มีคอลัมน์ <code>image_url</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    cols = st.columns(4)
    for i, row in df.iterrows():
        with cols[i % 4]:
            image_url = str(row.get("image_url", "") or "")
            title = str(row.get("title", "No title") or "No title")
            price = float(row.get("price", 0) or 0)
            currency = str(row.get("currency", "") or "")
            condition = str(row.get("condition", "") or "")
            source = str(row.get("source", "") or "")
            item_url = str(row.get("item_url", "") or "")

            img_html = f"<img class='card-img' src='{image_url}' />" if image_url else "<div class='card-img' style='display:flex;align-items:center;justify-content:center;color:#64748b;'>ไม่มีรูป</div>"
            link_html = f"<a href='{item_url}' target='_blank'>เปิดดูรายการ</a>" if item_url else ""
            thb = price * usd_to_thb if currency.upper() == "USD" or currency == "" else price

            st.markdown(
                f"""
                <div class='card'>
                    {img_html}
                    <div class='card-title'>{title[:110]}</div>
                    <div style='margin:8px 0;'>
                        <span class='pill'>{condition or 'Unknown'}</span>
                        <span class='pill'>{source}</span>
                    </div>
                    <div class='price'>{currency or 'USD'} {price:,.2f}</div>
                    <div class='price-thb'>ประมาณ ฿ {thb:,.2f}</div>
                    <div class='muted' style='margin-top:8px;'>{link_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


with st.sidebar:
    st.markdown("## 🔎 ค้นหาราคา")
    wave = st.selectbox("ซีรี่ส์ / Wave", KAYOU_WAVES, index=0)
    character = st.text_input("ชื่อตัวละคร", placeholder="Naruto / Sasuke / Itachi")
    rarity = st.selectbox("Rarity", KAYOU_RARITIES, index=0)
    card_no = st.text_input("เลขการ์ด", placeholder="เช่น NR-001, AR-12")
    extra_keyword = st.text_input("Keyword เพิ่มเติม", placeholder="EN / graded / PSA")
    usd_to_thb = st.number_input("USD → THB", min_value=1.0, max_value=100.0, value=36.0, step=0.25)
    max_results = st.slider("จำนวนรายการสูงสุด", 4, 80, 24, 4)
    st.markdown("---")
    data_source = st.radio("แหล่งข้อมูล", ["Search Link Only", "Manual Sold CSV", "eBay Active API"], index=0)
    ebay_token = ""
    uploaded_file = None
    if data_source == "eBay Active API":
        ebay_token = st.text_input("eBay Bearer Token", type="password", help="ต้องใช้ token จาก eBay Developer")
    if data_source == "Manual Sold CSV":
        uploaded_file = st.file_uploader("Upload CSV ที่มี image_url", type=["csv"])
    st.markdown("---")
    only_with_image = st.checkbox("แสดงเฉพาะรายการที่มีรูป", value=False)
    sort_by = st.selectbox("เรียงลำดับ", ["ค่าเริ่มต้น", "ราคาต่ำ → สูง", "ราคาสูง → ต่ำ"])

st.markdown(
    """
    <div class='hero'>
        <h1>🃏 Naruto Kayou Price Checker</h1>
        <p>ค้นหาราคา Kayou พร้อมแสดงรูปการ์ดในเว็บ / รองรับ eBay API และ CSV ที่มี image_url</p>
    </div>
    """,
    unsafe_allow_html=True,
)

query = build_query(wave, character, rarity, card_no, extra_keyword)
st.markdown(f"## Keyword ที่ใช้ค้นหา: `{query}`")

links = market_links(query)
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    st.link_button("เปิด eBay Active", links["eBay Active"], use_container_width=True)
with col2:
    st.link_button("เปิด eBay Sold", links["eBay Sold"], use_container_width=True)
with col3:
    st.link_button("เปิด 130point", links["130point"], use_container_width=True)
with col4:
    run_search = st.button("🔍 ค้นหาและแสดงรูป", type="primary", use_container_width=True)

if "results" not in st.session_state:
    st.session_state["results"] = pd.DataFrame()

if run_search:
    if data_source == "eBay Active API":
        if not ebay_token:
            st.warning("กรุณาใส่ eBay Bearer Token ก่อน เพื่อดึงรูปและรายการกลับมาแสดงในเว็บ")
        else:
            st.session_state["results"] = search_ebay_items(query, ebay_token, max_results)
    elif data_source == "Manual Sold CSV":
        if uploaded_file is None:
            st.warning("กรุณา Upload CSV ที่มีคอลัมน์ image_url")
        else:
            st.session_state["results"] = normalize_csv(pd.read_csv(uploaded_file))
    else:
        st.session_state["results"] = pd.DataFrame()
        st.info("Search Link Only จะเปิดลิงก์ตลาดเท่านั้น ถ้าต้องการให้รูปขึ้นในเว็บ ให้เลือก eBay Active API หรือ Manual Sold CSV")

results = clean_df(st.session_state.get("results", pd.DataFrame()), only_with_image, sort_by)

if not results.empty:
    prices = pd.to_numeric(results["price"], errors="coerce").dropna()
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("จำนวนรายการ", f"{len(results):,}")
    with m2:
        st.metric("ราคาต่ำสุด", f"{prices.min():,.2f}" if not prices.empty else "-")
    with m3:
        st.metric("ราคาเฉลี่ย", f"{prices.mean():,.2f}" if not prices.empty else "-")
    with m4:
        st.metric("ราคาสูงสุด", f"{prices.max():,.2f}" if not prices.empty else "-")

tab1, tab2, tab3 = st.tabs(["🖼️ รูปการ์ด", "📋 ตารางราคา", "📤 Export"])
with tab1:
    show_cards(results, usd_to_thb)

with tab2:
    if results.empty:
        st.info("ยังไม่มีข้อมูลตาราง")
    else:
        st.dataframe(results, use_container_width=True, hide_index=True)

with tab3:
    if results.empty:
        st.info("ยังไม่มีข้อมูลสำหรับ Export")
    else:
        st.download_button(
            "Download Excel",
            data=to_excel_bytes(results),
            file_name="naruto_kayou_price_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

st.caption("หมายเหตุ: eBay Active API ต้องใช้ Bearer Token จาก eBay Developer ส่วน eBay Sold แบบสดในเว็บนิยมใช้ลิงก์ Sold/130point หรือ CSV ที่บันทึกมาเอง")
