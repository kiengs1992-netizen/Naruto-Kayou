from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus
from html import escape

import pandas as pd
import streamlit as st

from card_catalog import DEFAULT_EXCLUDE_WORDS, KAYOU_RARITIES, KAYOU_SETS
from price_sources import (
    build_query,
    clean_market_noise,
    convert_to_thb,
    ebay_search_url,
    export_excel,
    fetch_ebay_active_listings,
    read_manual_csv,
    remove_outliers_iqr,
    summarize_prices,
)

st.set_page_config(
    page_title="Naruto Kayou Price Checker",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root{
        --bg:#f4f7fb;
        --card:#ffffff;
        --card2:#f9fbff;
        --text:#101828;
        --muted:#667085;
        --line:#e4e7ec;
        --blue:#2563eb;
        --blue2:#1d4ed8;
        --orange:#f97316;
        --green:#12b76a;
        --red:#f04438;
        --shadow:0 14px 38px rgba(16,24,40,.08);
        --soft-shadow:0 8px 24px rgba(16,24,40,.06);
    }
    html, body, [data-testid="stAppViewContainer"]{
        background: radial-gradient(circle at top left, #eaf1ff 0, #f4f7fb 32%, #f7f9fc 100%);
    }
    .block-container{
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1480px;
    }

    /* Sidebar: switch to light Microsoft-style panel so Thai labels and input text are easy to read */
    [data-testid="stSidebar"]{
        background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
        border-right: 1px solid #dbeafe;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"]{
        padding: 1.15rem .95rem;
    }
    [data-testid="stSidebar"] *{
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] h3{
        color:#1e3a8a !important;
        font-weight:800 !important;
        letter-spacing:-.02em;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stCaption{
        color:#172554 !important;
    }
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{
        color:#475569 !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="input"],
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] textarea{
        background:#ffffff !important;
        border:1px solid #bfdbfe !important;
        border-radius:12px !important;
        box-shadow:0 1px 2px rgba(16,24,40,.05) !important;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] div{
        color:#0f172a !important;
        -webkit-text-fill-color:#0f172a !important;
    }
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder{
        color:#64748b !important;
        opacity:1 !important;
        -webkit-text-fill-color:#64748b !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label p,
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label p{
        color:#0f172a !important;
        font-weight:600 !important;
    }
    [data-testid="stSidebar"] hr{
        border-color:#bfdbfe !important;
    }

    .hero{
        position:relative;
        overflow:hidden;
        padding: 28px 30px;
        border-radius: 28px;
        background:
            linear-gradient(135deg, rgba(37,99,235,.96) 0%, rgba(29,78,216,.94) 46%, rgba(15,23,42,.98) 100%);
        color:white;
        box-shadow: var(--shadow);
        margin-bottom: 20px;
    }
    .hero:after{
        content:"";
        position:absolute;
        width:320px;
        height:320px;
        right:-80px;
        top:-120px;
        border-radius:999px;
        background:rgba(249,115,22,.22);
    }
    .hero h1{
        font-size: 2.2rem;
        line-height: 1.15;
        margin:0 0 8px 0;
        letter-spacing:-.03em;
    }
    .hero p{
        font-size:1rem;
        opacity:.92;
        margin:0;
        max-width: 880px;
    }
    .hero-badges{
        display:flex;
        gap:10px;
        flex-wrap:wrap;
        margin-top:18px;
    }
    .badge{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding:8px 12px;
        border:1px solid rgba(255,255,255,.22);
        background:rgba(255,255,255,.13);
        border-radius:999px;
        font-size:.86rem;
        backdrop-filter: blur(8px);
    }
    .panel{
        background: var(--card);
        border:1px solid var(--line);
        border-radius:24px;
        padding:20px;
        box-shadow: var(--soft-shadow);
        margin-bottom:16px;
    }
    .panel-title{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:10px;
        margin-bottom:10px;
    }
    .panel-title h3{
        margin:0;
        font-size:1.08rem;
        letter-spacing:-.01em;
    }
    .small-note{color:var(--muted); font-size:.9rem; line-height:1.7;}
    .query-box{
        border:1px dashed #bfdbfe;
        background: #eff6ff;
        color:#1e3a8a;
        padding:14px 16px;
        border-radius:18px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        word-break:break-word;
    }
    .price-card{
        background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);
        border:1px solid var(--line);
        border-radius:22px;
        padding:18px;
        box-shadow: var(--soft-shadow);
        min-height:120px;
    }
    .price-card .label{color:var(--muted); font-size:.84rem; margin-bottom:8px;}
    .price-card .value{font-size:1.55rem; font-weight:800; color:var(--text); letter-spacing:-.03em;}
    .price-card .hint{font-size:.78rem; color:var(--muted); margin-top:8px;}
    .status-good{color:#027a48; background:#ecfdf3; border:1px solid #abefc6; border-radius:999px; padding:5px 10px; font-size:.8rem;}
    .status-warn{color:#b54708; background:#fffaeb; border:1px solid #fedf89; border-radius:999px; padding:5px 10px; font-size:.8rem;}
    .image-card{
        background:#ffffff;
        border:1px solid var(--line);
        border-radius:20px;
        overflow:hidden;
        box-shadow:var(--soft-shadow);
        height:100%;
    }
    .image-card-body{padding:12px 14px;}
    .image-title{font-weight:800; color:#101828; font-size:.92rem; line-height:1.35; min-height:48px;}
    .image-price{font-weight:900; color:#1d4ed8; font-size:1.05rem; margin-top:8px;}
    .image-meta{font-size:.78rem; color:#667085; margin-top:4px;}
    div[data-testid="stMetric"]{
        background: white;
        border: 1px solid var(--line);
        padding: 16px;
        border-radius: 20px;
        box-shadow: var(--soft-shadow);
    }
    .stButton > button, .stDownloadButton > button{
        border-radius: 14px !important;
        font-weight: 700 !important;
        border: 1px solid #d0d5dd !important;
    }
    .stLinkButton a{
        border-radius: 14px !important;
        font-weight: 700 !important;
    }
    [data-testid="stDataFrame"]{
        border-radius:18px;
        overflow:hidden;
        box-shadow: var(--soft-shadow);
    }
    .footer-warning{
        border:1px solid #fedf89;
        background:#fffaeb;
        color:#93370d;
        padding:14px 16px;
        border-radius:18px;
        margin-top:18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Header
# -------------------------
st.markdown(
    """
    <div class="hero">
      <h1>🌀 Naruto Kayou Price Checker</h1>
      <p>เช็คราคาการ์ด Kayou แบบใช้งานง่าย เลือกรุ่น / ตัวละคร / Rarity แล้วเปิดตลาดทันที หรือดึงข้อมูลเข้า Dashboard เพื่อคำนวณราคากลางเป็นบาท</p>
      <div class="hero-badges">
        <span class="badge">⚡ Quick Search</span>
        <span class="badge">📊 Median Market Price</span>
        <span class="badge">🧹 Clean Noise / Outlier</span>
        <span class="badge">📥 Export Excel</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Sidebar inputs
# -------------------------
with st.sidebar:
    st.markdown("### 🔍 Search Control")
    st.caption("เลือกข้อมูลหลักของการ์ด แล้วระบบจะสร้างคำค้นให้อัตโนมัติ")

    set_names = [x["series"] for x in KAYOU_SETS]
    selected_set_name = st.selectbox("รุ่น / Set", set_names, index=0)
    selected_set = next(x for x in KAYOU_SETS if x["series"] == selected_set_name)

    custom_set = st.text_input("หรือใส่ชื่อรุ่นเอง", placeholder="เช่น Naruto Kayou T4W7 Jin Chapter")
    character = st.text_input("ชื่อตัวละคร", placeholder="Naruto / Sasuke / Itachi")
    rarity = st.selectbox("Rarity", ["All / ไม่ระบุ"] + KAYOU_RARITIES, index=0)
    card_no = st.text_input("เลขการ์ด", placeholder="เช่น NR-001, AR-12, BP-...")
    extra_keywords = st.text_input("Keyword เพิ่มเติม", placeholder="graded PSA 10 / English / Chinese")

    st.divider()
    st.markdown("### 🧾 Data Source")
    source_mode = st.radio(
        "แหล่งข้อมูล",
        ["Search Link Only", "Manual Sold CSV", "eBay Active API"],
        index=0,
        help="แนะนำให้ใช้ Sold CSV สำหรับราคาจริง และใช้ Active API สำหรับดูราคาตั้งขายปัจจุบัน",
    )
    limit = st.slider("จำนวนรายการสูงสุด", 10, 200, 50, 10)

    st.divider()
    st.markdown("### 💱 Exchange Rate")
    usd_thb = st.number_input("USD → THB", value=36.5, min_value=0.0, step=0.1)
    jpy_thb = st.number_input("JPY → THB", value=0.25, min_value=0.0, step=0.01)
    cny_thb = st.number_input("CNY → THB", value=5.05, min_value=0.0, step=0.05)
    remove_outliers = st.checkbox("ตัดราคาหลุดตลาดด้วย IQR", value=True)
    show_images = st.checkbox("แสดงรูปการ์ดในผลลัพธ์", value=True, help="แสดงได้เมื่อ eBay API หรือ CSV มี column image_url")

    st.divider()
    with st.expander("คำที่ต้องการตัดออก", expanded=False):
        exclude_text = st.text_area("Exclude words", value="\n".join(DEFAULT_EXCLUDE_WORDS), height=120)

series_alias = custom_set.strip() or selected_set["search_alias"]
rarity_value = "" if rarity.startswith("All") else rarity
query = build_query(series_alias, character, rarity_value, card_no, extra_keywords)
exclude_words = [x.strip() for x in exclude_text.splitlines() if x.strip()]

# -------------------------
# Quick action panels
# -------------------------
left, right = st.columns([1.15, .85], gap="large")

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title"><h3>🎯 คำค้นปัจจุบัน</h3><span class="status-good">Ready</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="query-box">{query}</div>', unsafe_allow_html=True)
    st.caption(f"หมายเหตุ Set: {selected_set.get('note','-')}")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.link_button("eBay Active", ebay_search_url(query, sold=False), use_container_width=True)
    with a2:
        st.link_button("eBay Sold", ebay_search_url(query, sold=True), use_container_width=True)
    with a3:
        st.link_button("130point Search", f"https://130point.com/sales/?search={quote_plus(query)}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title"><h3>✅ วิธีใช้งานเร็ว</h3><span class="status-warn">Tip</span></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="small-note">
        1) เลือกรุ่น + ตัวละคร + rarity<br>
        2) กด eBay Sold / 130point เพื่อดูราคาขายจริง<br>
        3) ถ้ามี CSV ให้ Upload เพื่อคำนวณราคากลาง<br>
        4) ใช้ Median เป็นราคาตลาดที่ปลอดภัยกว่า Average
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Data loading
# -------------------------
result_df = pd.DataFrame()
error_box = None

if source_mode == "eBay Active API":
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title"><h3>⚡ eBay Active API</h3><span class="status-warn">Token Required</span></div>', unsafe_allow_html=True)
    st.info("โหมดนี้ต้องใส่ EBAY_OAUTH_TOKEN ใน .streamlit/secrets.toml หรือ Environment variable")
    try:
        token = st.secrets.get("EBAY_OAUTH_TOKEN", "")
    except Exception:
        token = ""
    import os
    token = token or os.getenv("EBAY_OAUTH_TOKEN", "")
    if st.button("ดึงราคา eBay Active", type="primary", use_container_width=True):
        try:
            result_df = fetch_ebay_active_listings(query, token, limit=limit)
        except Exception as e:
            error_box = str(e)
    st.markdown('</div>', unsafe_allow_html=True)

elif source_mode == "Manual Sold CSV":
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title"><h3>📥 Upload Sold Price CSV</h3><span class="status-good">Recommended</span></div>', unsafe_allow_html=True)
    st.caption("Column ขั้นต่ำ: title, price | แนะนำเพิ่ม currency, shipping, sold_date, item_url, condition, image_url")
    uploaded = st.file_uploader("ลากไฟล์ CSV มาวางตรงนี้", type=["csv"])
    if uploaded is not None:
        try:
            result_df = read_manual_csv(uploaded)
        except Exception as e:
            error_box = str(e)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title"><h3>🔗 Search Link Mode</h3><span class="status-good">No Setup Needed</span></div>', unsafe_allow_html=True)
    st.caption("โหมดนี้ไม่ต้องใช้ Token เหมาะสำหรับเปิดตลาดเช็คราคาเร็ว ๆ หากต้องการ Dashboard ให้เลือก Manual Sold CSV หรือ eBay Active API")
    st.markdown('</div>', unsafe_allow_html=True)

if error_box:
    st.error(error_box)

# -------------------------
# Results dashboard
# -------------------------
if result_df.empty:
    demo_cols = st.columns(4)
    demo_items = [
        ("ตลาดจริง", "ดู Sold ก่อน Active", "ลดโอกาสตั้งราคาสูงเกินจริง"),
        ("สภาพการ์ด", "Raw / PSA / BGS", "เกรดมีผลกับราคามาก"),
        ("ภาษา", "Chinese / English", "บางรุ่น demand ไม่เท่ากัน"),
        ("เลขการ์ด", "Card No.", "ช่วยลดผลค้นหาผิดใบ"),
    ]
    for col, (label, value, hint) in zip(demo_cols, demo_items):
        with col:
            st.markdown(
                f'<div class="price-card"><div class="label">{label}</div><div class="value">{value}</div><div class="hint">{hint}</div></div>',
                unsafe_allow_html=True,
            )
else:
    cleaned = clean_market_noise(result_df, exclude_words)
    cleaned = convert_to_thb(cleaned, usd_thb=usd_thb, jpy_thb=jpy_thb, cny_thb=cny_thb)
    raw_count = len(cleaned)
    if remove_outliers:
        cleaned = remove_outliers_iqr(cleaned, "total_thb")
    summary = summarize_prices(cleaned, "total_thb")

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title"><h3>📊 สรุปราคาตลาด</h3><span class="status-good">Calculated</span></div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("จำนวนรายการ", f"{summary.count}")
    m2.metric("ต่ำสุด", f"{summary.min_price:,.0f} THB" if summary.min_price is not None else "-")
    m3.metric("ราคากลาง", f"{summary.median_price:,.0f} THB" if summary.median_price is not None else "-")
    m4.metric("เฉลี่ย", f"{summary.avg_price:,.0f} THB" if summary.avg_price is not None else "-")
    m5.metric("สูงสุด", f"{summary.max_price:,.0f} THB" if summary.max_price is not None else "-")
    if remove_outliers and raw_count != len(cleaned):
        st.caption(f"ตัดรายการราคาหลุดตลาดออก {raw_count - len(cleaned)} รายการ")
    st.markdown('</div>', unsafe_allow_html=True)

    table_tab, gallery_tab, chart_tab, export_tab = st.tabs(["🧾 รายการราคา", "🖼️ รูปการ์ด", "📈 กราฟ", "📥 Export"])
    with table_tab:
        show_cols = [c for c in ["source", "title", "condition", "price", "shipping", "currency", "total_thb", "seller", "raw_date", "item_url"] if c in cleaned.columns]
        st.dataframe(cleaned[show_cols], use_container_width=True, hide_index=True)
    with gallery_tab:
        if not show_images:
            st.info("เปิดตัวเลือก 'แสดงรูปการ์ดในผลลัพธ์' ที่ Sidebar ก่อน")
        elif "image_url" not in cleaned.columns or cleaned["image_url"].fillna("").astype(str).str.strip().eq("").all():
            st.info("ยังไม่มีรูปภาพให้แสดง: ใช้โหมด eBay Active API หรือใส่ column image_url ใน CSV")
        else:
            image_rows = cleaned[cleaned["image_url"].fillna("").astype(str).str.strip().ne("")].head(24)
            cols = st.columns(4)
            for idx, (_, row) in enumerate(image_rows.iterrows()):
                with cols[idx % 4]:
                    st.markdown('<div class="image-card">', unsafe_allow_html=True)
                    st.image(str(row.get("image_url", "")), use_container_width=True)
                    title = escape(str(row.get("title", ""))[:90])
                    price_txt = f"{float(row.get('total_thb', 0)):,.0f} THB" if pd.notna(row.get("total_thb", None)) else "-"
                    meta = escape(f"{row.get('condition','') or ''} · {row.get('source','') or ''}")
                    st.markdown(f'<div class="image-card-body"><div class="image-title">{title}</div><div class="image-price">{price_txt}</div><div class="image-meta">{meta}</div></div>', unsafe_allow_html=True)
                    if str(row.get("item_url", "")).strip():
                        st.link_button("เปิดรายการ", str(row.get("item_url")), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
    with chart_tab:
        if "total_thb" in cleaned.columns and len(cleaned) > 1:
            chart_df = cleaned.sort_values("total_thb").reset_index(drop=True)
            chart_df["item_no"] = chart_df.index + 1
            st.line_chart(chart_df, x="item_no", y="total_thb", use_container_width=True)
        else:
            st.info("ต้องมีข้อมูลมากกว่า 1 รายการจึงจะแสดงกราฟได้")
    with export_tab:
        out_path = Path("naruto_kayou_price_report.xlsx")
        export_excel(cleaned, summary, query, str(out_path))
        st.download_button(
            "Download Excel Report",
            data=out_path.read_bytes(),
            file_name="naruto_kayou_price_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

st.markdown(
    """
    <div class="footer-warning">
    <b>คำเตือน:</b> ราคาการ์ดสะสมผันผวนสูง ควรดู Sold Price มากกว่า Active Listing และตรวจสภาพ / ภาษา / เกรด / เลขการ์ดก่อนซื้อขายทุกครั้ง
    </div>
    """,
    unsafe_allow_html=True,
)
