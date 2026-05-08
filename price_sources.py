from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import requests


@dataclass
class PriceSummary:
    count: int
    min_price: float | None
    median_price: float | None
    avg_price: float | None
    max_price: float | None


def build_query(series_alias: str, character: str = "", rarity: str = "", card_no: str = "", extra: str = "") -> str:
    parts = [series_alias or "Naruto Kayou"]
    for value in [character, rarity, card_no, extra]:
        value = (value or "").strip()
        if value:
            parts.append(value)
    return " ".join(parts)


def ebay_search_url(query: str, sold: bool = False) -> str:
    params = {"_nkw": query, "_sacat": "0", "LH_PrefLoc": "2"}
    if sold:
        params.update({"LH_Sold": "1", "LH_Complete": "1"})
    return "https://www.ebay.com/sch/i.html?" + urlencode(params)


def _extract_price(price_obj: dict[str, Any] | None) -> tuple[float | None, str]:
    if not price_obj:
        return None, ""
    try:
        return float(price_obj.get("value")), price_obj.get("currency", "")
    except Exception:
        return None, price_obj.get("currency", "") if isinstance(price_obj, dict) else ""


def fetch_ebay_active_listings(query: str, oauth_token: str, marketplace: str = "EBAY_US", limit: int = 50) -> pd.DataFrame:
    """Fetch active eBay listings using official Buy Browse API.

    Requires OAuth application token in EBAY_OAUTH_TOKEN or Streamlit secrets.
    """
    if not oauth_token:
        raise ValueError("ยังไม่ได้ใส่ EBAY_OAUTH_TOKEN")

    endpoint = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace,
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "limit": min(max(int(limit), 1), 200),
        "sort": "price",
    }
    response = requests.get(endpoint, headers=headers, params=params, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"eBay API error {response.status_code}: {response.text[:500]}")
    data = response.json()
    rows: list[dict[str, Any]] = []
    for item in data.get("itemSummaries", []):
        price, currency = _extract_price(item.get("price"))
        shipping, shipping_currency = _extract_price((item.get("shippingOptions") or [{}])[0].get("shippingCost"))
        total = None
        if price is not None:
            total = price + (shipping or 0)
        rows.append({
            "source": "eBay Active",
            "title": item.get("title"),
            "price": price,
            "shipping": shipping,
            "total_price": total,
            "currency": currency or shipping_currency,
            "condition": item.get("condition"),
            "seller": (item.get("seller") or {}).get("username"),
            "item_url": item.get("itemWebUrl"),
            "image_url": (item.get("image") or {}).get("imageUrl"),
            "raw_date": "",
        })
    return pd.DataFrame(rows)


def read_manual_csv(file) -> pd.DataFrame:
    """Read sold/manual comp CSV.

    Required or accepted columns: title, price, currency, source, item_url, sold_date/raw_date, condition.
    """
    df = pd.read_csv(file)
    cols = {c.lower().strip(): c for c in df.columns}
    if "price" not in cols:
        raise ValueError("CSV ต้องมี column ชื่อ price")
    normalized = pd.DataFrame()
    normalized["source"] = df[cols.get("source", df.columns[0])] if "source" in cols else "Manual CSV"
    normalized["title"] = df[cols.get("title", df.columns[0])] if "title" in cols else ""
    normalized["price"] = pd.to_numeric(df[cols["price"]], errors="coerce")
    normalized["shipping"] = pd.to_numeric(df[cols["shipping"]], errors="coerce") if "shipping" in cols else 0
    normalized["total_price"] = normalized["price"].fillna(0) + normalized["shipping"].fillna(0)
    normalized["currency"] = df[cols.get("currency", df.columns[0])] if "currency" in cols else "USD"
    normalized["condition"] = df[cols.get("condition", df.columns[0])] if "condition" in cols else ""
    normalized["seller"] = df[cols.get("seller", df.columns[0])] if "seller" in cols else ""
    normalized["item_url"] = df[cols.get("item_url", df.columns[0])] if "item_url" in cols else ""
    normalized["image_url"] = df[cols.get("image_url", df.columns[0])] if "image_url" in cols else ""
    normalized["raw_date"] = df[cols.get("sold_date", cols.get("raw_date", df.columns[0]))] if ("sold_date" in cols or "raw_date" in cols) else ""
    return normalized


def clean_market_noise(df: pd.DataFrame, exclude_words: list[str] | None = None) -> pd.DataFrame:
    if df.empty:
        return df
    exclude_words = exclude_words or []
    output = df.copy()
    output = output[output["total_price"].notna() & (output["total_price"] > 0)]
    for word in exclude_words:
        word = word.strip().lower()
        if not word:
            continue
        output = output[~output["title"].fillna("").str.lower().str.contains(re.escape(word), na=False)]
    return output.reset_index(drop=True)


def convert_to_thb(df: pd.DataFrame, usd_thb: float = 36.5, jpy_thb: float = 0.25, cny_thb: float = 5.05) -> pd.DataFrame:
    if df.empty:
        return df
    rates = {"USD": usd_thb, "US": usd_thb, "JPY": jpy_thb, "CNY": cny_thb, "RMB": cny_thb, "THB": 1.0}
    out = df.copy()
    out["currency"] = out["currency"].fillna("USD").astype(str).str.upper()
    out["rate_to_thb"] = out["currency"].map(rates).fillna(usd_thb)
    out["total_thb"] = out["total_price"].astype(float) * out["rate_to_thb"]
    return out


def summarize_prices(df: pd.DataFrame, price_col: str = "total_thb") -> PriceSummary:
    if df.empty or price_col not in df:
        return PriceSummary(0, None, None, None, None)
    values = pd.to_numeric(df[price_col], errors="coerce").dropna()
    if values.empty:
        return PriceSummary(0, None, None, None, None)
    return PriceSummary(
        count=int(values.count()),
        min_price=float(values.min()),
        median_price=float(values.median()),
        avg_price=float(values.mean()),
        max_price=float(values.max()),
    )


def remove_outliers_iqr(df: pd.DataFrame, price_col: str = "total_thb") -> pd.DataFrame:
    if df.empty or len(df) < 5:
        return df
    values = pd.to_numeric(df[price_col], errors="coerce")
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0 or math.isnan(iqr):
        return df
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return df[(values >= low) & (values <= high)].reset_index(drop=True)


def export_excel(df: pd.DataFrame, summary: PriceSummary, query: str, output_path: str) -> str:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        meta = pd.DataFrame([
            {"field": "query", "value": query},
            {"field": "checked_at", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"field": "count", "value": summary.count},
            {"field": "min_thb", "value": summary.min_price},
            {"field": "median_thb", "value": summary.median_price},
            {"field": "avg_thb", "value": summary.avg_price},
            {"field": "max_thb", "value": summary.max_price},
        ])
        meta.to_excel(writer, index=False, sheet_name="Summary")
        df.to_excel(writer, index=False, sheet_name="Listings")
    return output_path
