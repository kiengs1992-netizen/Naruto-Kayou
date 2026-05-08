from __future__ import annotations

KAYOU_RARITIES = [
    "R", "TR", "SR", "SSR", "HR", "TGR", "UR", "AR", "OR", "ZR", "SLR", "PTR", "PU", "CP", "LR",
    "SP", "MR", "BP", "GP", "SE", "CR", "NR", "XR", "QR", "PR", "Promo", "Other"
]

# Seed catalog. The app also lets users type any custom set/series.
# Keep names search-friendly rather than pretending this is an official exhaustive database.
KAYOU_SETS = [
    {"series": "All / ไม่ระบุรุ่น", "search_alias": "Naruto Kayou", "note": "ค้นรวมทุกรุ่น"},
    {"series": "Chinese T1W1", "search_alias": "Naruto Kayou T1W1", "note": "Tier 1 Wave 1"},
    {"series": "Chinese T1W2", "search_alias": "Naruto Kayou T1W2", "note": "Tier 1 Wave 2"},
    {"series": "Chinese T1W3", "search_alias": "Naruto Kayou T1W3", "note": "Tier 1 Wave 3"},
    {"series": "Chinese T1W4", "search_alias": "Naruto Kayou T1W4", "note": "Tier 1 Wave 4"},
    {"series": "Chinese T1W5", "search_alias": "Naruto Kayou T1W5", "note": "Tier 1 Wave 5"},
    {"series": "Chinese T2W1", "search_alias": "Naruto Kayou T2W1", "note": "Tier 2 Wave 1"},
    {"series": "Chinese T2W2", "search_alias": "Naruto Kayou T2W2", "note": "Tier 2 Wave 2"},
    {"series": "Chinese T2W3", "search_alias": "Naruto Kayou T2W3", "note": "Tier 2 Wave 3"},
    {"series": "Chinese T2W4", "search_alias": "Naruto Kayou T2W4", "note": "Tier 2 Wave 4"},
    {"series": "Chinese T2W5", "search_alias": "Naruto Kayou T2W5", "note": "Tier 2 Wave 5"},
    {"series": "Chinese T2W6", "search_alias": "Naruto Kayou T2W6", "note": "Tier 2 Wave 6"},
    {"series": "Chinese T2W7", "search_alias": "Naruto Kayou T2W7", "note": "Tier 2 Wave 7"},
    {"series": "Chinese T2W8 / English Earth Scroll", "search_alias": "Naruto Kayou T2W8 Earth Scroll", "note": "English mapping may vary by seller listing"},
    {"series": "Chinese T3W1", "search_alias": "Naruto Kayou T3W1", "note": "Tier 3 Wave 1"},
    {"series": "Chinese T3W2", "search_alias": "Naruto Kayou T3W2", "note": "Tier 3 Wave 2"},
    {"series": "Chinese T3W3", "search_alias": "Naruto Kayou T3W3", "note": "Tier 3 Wave 3"},
    {"series": "Chinese T3W4", "search_alias": "Naruto Kayou T3W4", "note": "Tier 3 Wave 4"},
    {"series": "Chinese T3W5", "search_alias": "Naruto Kayou T3W5", "note": "Tier 3 Wave 5"},
    {"series": "Chinese T4W1", "search_alias": "Naruto Kayou T4W1", "note": "Tier 4 Wave 1"},
    {"series": "Chinese T4W2", "search_alias": "Naruto Kayou T4W2", "note": "Tier 4 Wave 2"},
    {"series": "Chinese T4W3", "search_alias": "Naruto Kayou T4W3", "note": "Tier 4 Wave 3"},
    {"series": "Chinese T4W4", "search_alias": "Naruto Kayou T4W4", "note": "Tier 4 Wave 4"},
    {"series": "Chinese T4W5", "search_alias": "Naruto Kayou T4W5", "note": "Tier 4 Wave 5"},
    {"series": "Chinese T4W6 / English Heaven Scroll", "search_alias": "Naruto Kayou T4W6 Heaven Scroll", "note": "English Series 1 commonly mapped to T4W6"},
    {"series": "Chinese T4W7 / English Jin Chapter", "search_alias": "Naruto Kayou T4W7 Jin Chapter", "note": "English Series 2 commonly mapped to T4W7"},
    {"series": "Promo / Event / PR", "search_alias": "Naruto Kayou Promo PR", "note": "โปรโม / งานอีเวนต์"},
]

DEFAULT_EXCLUDE_WORDS = [
    "fan art", "proxy", "custom", "digital", "reprint", "sticker", "poster", "booster box", "box only", "empty box"
]
