import re


def vietnamese_to_number(text: str) -> int | None:
    """
    Convert Vietnamese number words -> integer.
    Hỗ trợ: trăm, mươi, lẻ/linh/ninh/nẻ, nghìn/ngàn, triệu, tỷ.
    """
    if not text:
        return None
    tokens = text.lower().split()

    # sửa lỗi chính tả thường gặp
    typo_map = {"ninh": "linh", "nẻ": "lẻ", "mưoi": "mươi"}
    tokens = [typo_map.get(tok, tok) for tok in tokens]

    units_map = {
        "không": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3,
        "bốn": 4, "tư": 4, "năm": 5, "lăm": 5, "sáu": 6,
        "bảy": 7, "tám": 8, "chín": 9
    }
    scales_map = {"tỷ": 10**9, "triệu": 10**6, "nghìn": 10**3, "ngàn": 10**3}

    total, group = 0, 0
    i, L = 0, len(tokens)

    while i < L:
        t = tokens[i]

        # Hàng trăm
        if t in units_map and i + 1 < L and tokens[i + 1] == "trăm":
            group += units_map[t] * 100
            i += 2
            continue
        if t == "trăm":
            group += 100
            i += 1
            continue

        # Hàng chục
        if t in units_map and i + 1 < L and tokens[i + 1] == "mươi":
            group += units_map[t] * 10
            i += 2
            continue
        if t == "mươi":
            group += 10
            i += 1
            continue

        # Mười
        if t == "mười":
            group += 10
            i += 1
            continue

        # Bỏ qua "lẻ/linh"
        if t in ("lẻ", "linh"):
            i += 1
            continue

        # Đơn vị
        if t in units_map:
            group += units_map[t]
            i += 1
            continue

        # Lớp nghìn/triệu/tỷ
        if t in scales_map:
            scale_val = scales_map[t]
            if group == 0:
                group = 1
            total += group * scale_val
            group = 0
            i += 1
            continue

        i += 1

    total += group
    return total if total != 0 else None
# --------------------
# (Re-using improved vocab/patterns/parsers from previous code)
NUM_WORDS_SIMPLE = [
    "không","một","mốt","hai","ba","bốn","tư","năm","lăm",
    "sáu","bảy","tám","chín","mười","mươi","trăm","nghìn", "ngàn",
    "triệu","tỷ","linh","lẻ","phẩy", "ninh", "nẻ"
]

PHONE_DIGIT_WORDS = ["không","một","hai","ba","bốn","năm","sáu","bảy","tám","chín"]

PHONE_WORD_ALT = r"(?:\d+|" + r"|".join(re.escape(w) for w in PHONE_DIGIT_WORDS) + r")"


UNIT_CURRENCY = ["đồng", "đô la", "usd", "vnd"]
UNIT_MEASURE = ["m", "km", "kg", "cm", "mm", "l", "lit"]
ORDINAL_WORDS = {"nhất": 1, "nhì": 2, "thứ nhất": 1, "thứ nhì": 2, "thứ ba": 3, "thứ tư": 4}

NUM_WORD_ALT = r"(?:\d+|" + r"|".join(re.escape(w) for w in NUM_WORDS_SIMPLE) + r")"
# NUM_SEQ = r"(?:{nw}(?:\s+{nw})*)".format(nw=NUM_WORD_ALT)
NUM_SEQ = r"(?:{nw}(?:\s+{nw})+)".format(nw=NUM_WORD_ALT)

DIGIT_SEQ = r"(?:\d{1,3}(?:[.,]\d{3})*|\d+)"  # cho số 100, 15.800, 1,200,000
NUM_OR_WORD_SEQ = r"(?:" + DIGIT_SEQ + r"|" + NUM_WORD_ALT + r")(?:\s+(?:" + DIGIT_SEQ + r"|" + NUM_WORD_ALT + r"))*"


# Patterns (priority)
_PATTERNS = [
    ("decimal", re.compile(r"\b" + NUM_SEQ + r"\s+phẩy\s+" + NUM_SEQ + r"\b", flags=re.I)),
    ("date", re.compile(r"\bngày\s+" + NUM_SEQ + r"\s+tháng\s+" + NUM_SEQ + r"\s+năm\s+" + NUM_SEQ, flags=re.I)),
    ("date", re.compile(r"\bngày\s+" + NUM_SEQ + r"\s+tháng\s+" + NUM_SEQ, flags=re.I)),
    ("date", re.compile(r"\btháng\s+" + NUM_SEQ + r"\s+năm\s+" + NUM_SEQ, flags=re.I)),
    ("time", re.compile(r"\b" + NUM_SEQ + r"\s+giờ(?:\s+" + NUM_SEQ + r"\s+phút)?(?:\s+" + NUM_SEQ + r"\s+giây)?", flags=re.I)),
    ("phone/account", re.compile(r"\b(?:(?:" + PHONE_WORD_ALT + r")\s+){1,}(?:" + PHONE_WORD_ALT + r")\b", flags=re.I)),
    
    ("currency", re.compile(r"\b" + NUM_OR_WORD_SEQ + r"\s+(?:" + "|".join(re.escape(u) for u in UNIT_CURRENCY) + r")\b", flags=re.I)),
    
    ("percentage", re.compile(r"\b" + NUM_SEQ + r"\s+(?:phần\s+trăm|%)\b", flags=re.I)),
    ("measurement", re.compile(r"\b" + NUM_SEQ + r"\s+(?:" + "|".join(re.escape(u) for u in UNIT_MEASURE) + r")\b", flags=re.I)),
    ("fraction", re.compile(r"\bphần\s+" + NUM_SEQ + r"\b", flags=re.I)),
    ("fraction", re.compile(r"\b" + NUM_SEQ + r"\s+phần\b", flags=re.I)),
    # ("ordinal", re.compile(r"\b(?:(?:thứ|hạng)\s+" + NUM_SEQ + r"|\b(?:" + "|".join(re.escape(k) for k in ORDINAL_WORDS.keys()) + r"))\b", flags=re.I)),
    ("number_sequence", re.compile(r"\b" + NUM_SEQ + r"\b", flags=re.I)),
]

# Vietnamese number maps
VI_NUM_MAP = {
    "không":0, "một":1, "mốt":1, "hai":2, "ba":3, "bốn":4, "tư":4,
    "năm":5, "lăm":5, "sáu":6, "bảy":7, "tám":8, "chín":9
}
UNIT_MAP = {"mươi":10, "mười":10, "trăm":100, "nghìn":1000, "triệu":1000000, "tỷ":1000000000}

# overlap helper
def _overlaps(existing_spans, start, end):
    for a,b in existing_spans:
        if not (end <= a or start >= b):
            return True
    return False

# pre-detect: 'cách đây <num> năm'
def predetect_specials(text):
    ents=[]
    for m in re.finditer(r"\bcách đây\s+" + NUM_SEQ + r"\s+năm\b", text, flags=re.I):
        ents.append({"text": m.group().strip(), "case":"year_duration", "start":m.span()[0], "end":m.span()[1]})
    return ents

# merge helper and connector pattern
_NUM_CONNECTORS_RE = re.compile(r'^[\s]*(?:và|,|với|mươi|trăm|nghìn|triệu|tỷ|lẻ|linh|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mốt|lăm|mười|\d+)[\s]*$', flags=re.I)


def merge_adjacent_entities(entities, text):
    if not entities:
        return []
    merged = []
    prev = entities[0]
    for cur in entities[1:]:
        gap = text[prev["end"]:cur["start"]]
        # nếu cả prev và cur đều là number_sequence thì merge luôn
        if prev["case"] == "number_sequence" and cur["case"] == "number_sequence":
            combined_text = text[prev["start"]:cur["end"]].strip()
            prev = {
                "text": combined_text,
                "case": "number_sequence",
                "start": prev["start"],
                "end": cur["end"]
            }
            continue
        # rule cũ (khoảng trắng, connector)
        if gap.strip() == "" or _NUM_CONNECTORS_RE.match(gap):
            combined_text = text[prev["start"]:cur["end"]].strip()
            prev = {
                "text": combined_text,
                "case": prev["case"],
                "start": prev["start"],
                "end": cur["end"]
            }
        else:
            merged.append(prev)
            prev = cur
    merged.append(prev)
    return merged


# detection core
def detect_number_entities(text):
    if not text:
        return []
    txt=text.strip()
    results=[]; occupied=[]
    for pe in predetect_specials(txt):
        results.append(pe); occupied.append((pe["start"], pe["end"]))
    for case, pattern in _PATTERNS:
        for m in pattern.finditer(txt):
            s,e=m.span()
            if _overlaps(occupied, s, e): continue
            results.append({"text":m.group().strip(), "case":case, "start":s, "end":e})
            occupied.append((s,e))
    results.sort(key=lambda x: x["start"])
    merged = merge_adjacent_entities(results, txt)
    return merged

# normalization helpers
def normalize_decimal(span_text):
    m=re.search(r"(" + NUM_SEQ + r")\s+phẩy\s+(" + NUM_SEQ + r")", span_text, flags=re.I)
    if not m: return span_text
    l,r=m.group(1),m.group(2)
    ln=vietnamese_to_number(l) if l else None
    rn=vietnamese_to_number(r) if r else None
    if ln is None and re.fullmatch(r"(?:\d+\s*)+", l): ln=int(l.replace(" ",""))
    if rn is None and re.fullmatch(r"(?:\d+\s*)+", r): rn=int(r.replace(" ",""))
    if ln is not None and rn is not None: return f"{ln}.{rn}"
    return span_text

def normalize_date(span_text):
    m=re.search(r"ngày\s+(.+?)\s+tháng\s+(.+?)\s+năm\s+(.+)", span_text, flags=re.I)
    if m:
        d_s,mo_s,y_s = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        d=vietnamese_to_number(d_s); mo=vietnamese_to_number(mo_s); y=vietnamese_to_number(y_s)
        if d is not None and mo is not None and y is not None:
            return f"{d:02d}/{mo:02d}/{y}"
    m2=re.search(r"ngày\s+(.+?)\s+tháng\s+(.+)", span_text, flags=re.I)
    if m2:
        d_s,mo_s = m2.group(1).strip(), m2.group(2).strip()
        d=vietnamese_to_number(d_s); mo=vietnamese_to_number(mo_s)
        if d is not None and mo is not None: return f"{d:02d}/{mo:02d}"
    return span_text

def normalize_time(span_text):
    m=re.search(r"(" + NUM_SEQ + r")\s+giờ(?:\s+(" + NUM_SEQ + r")\s+phút)?(?:\s+(" + NUM_SEQ + r")\s+giây)?", span_text, flags=re.I)
    if not m: return span_text
    h_s,m_s,s_s = m.group(1), m.group(2), m.group(3)
    h=vietnamese_to_number(h_s) if h_s else None
    mm=vietnamese_to_number(m_s) if m_s else 0
    ss=vietnamese_to_number(s_s) if s_s else None
    if h is not None:
        return f"{h:02d}:{(mm or 0):02d}" + (f":{ss:02d}" if ss is not None else "")
    return span_text

def normalize_percentage(span_text):
    m=re.search(r"(" + NUM_SEQ + r")\s*(?:phần\s+trăm|%)", span_text, flags=re.I)
    if not m: return span_text
    num=vietnamese_to_number(m.group(1))
    if num is not None: return f"{num}%"
    return span_text



def normalize_currency(span_text):
    # bắt đơn vị
    umatch = re.search(r"(đồng|đô la|usd|vnd)\b", span_text, flags=re.I)
    unit = umatch.group(1) if umatch else ""
    left = re.sub(r"(đồng|đô la|usd|vnd)\b", "", span_text, flags=re.I).strip()

    # --- trường hợp là số digit ---
    left_digits = left.replace(".", "").replace(",", "").replace(" ", "")
    if re.fullmatch(r"\d+", left_digits):
        return f"{int(left_digits)} {unit}".strip()

    # --- trường hợp có cả số và scale ---
    # ví dụ: "2 triệu", "5 tỷ"
    tokens = left.split()
    if len(tokens) == 2 and re.fullmatch(r"\d+", tokens[0]):
        num = int(tokens[0])
        scale = tokens[1].lower()
        scale_map = {
            "trăm": 10**2,
            "nghìn": 10**3, "ngàn": 10**3,
            "triệu": 10**6,
            "tỷ": 10**9
        }
        if scale in scale_map:
            return f"{num * scale_map[scale]} {unit}".strip()

    # --- trường hợp là chữ (hai triệu, năm tỷ, ...) ---
    num = vietnamese_to_number(left)
    if num is not None and num != 0:
        return f"{num} {unit}".strip()

    return span_text



def normalize_phone(span_text):
    tokens = span_text.lower().strip().split()
    digits = []
    for t in tokens:
        if re.fullmatch(r"\d+", t):  # số đã viết liền (vd: 545433)
            digits.extend(list(t))   # tách thành từng digit
        elif t in VI_NUM_MAP:        # số đọc bằng chữ
            digits.append(str(VI_NUM_MAP[t]))
        # bỏ qua từ không hợp lệ
    return "".join(digits) if digits else span_text




def normalize_number_sequence(span_text: str) -> str:
    """
    Normalize cụm số tiếng Việt -> digit string.
    """
    s = span_text.lower().strip()

    # chuẩn hoá lỗi chính tả
    typo_map = {"ninh": "linh", "nẻ": "lẻ", "mưoi": "mươi", "mưoii": "mươi"}
    for k, v in typo_map.items():
        s = s.replace(k, v)

    # Nếu toàn số digits (có space hoặc dấu chấm phẩy)
    if re.fullmatch(r"(?:\d+[\s.,]*)+", s):
        return re.sub(r"[\s.,]", "", s)

    # Tính bằng hàm vietnamese_to_number
    num = vietnamese_to_number(s)
    if num is not None:
        return str(num)

    return span_text



def normalize_fraction(span_text):
    m=re.search(r"phần\s+(" + NUM_SEQ + r")", span_text, flags=re.I)
    if m:
        denom=vietnamese_to_number(m.group(1))
        if denom: return f"1/{denom}"
    m2=re.search(r"(" + NUM_SEQ + r")\s+phần", span_text, flags=re.I)
    if m2:
        num=vietnamese_to_number(m2.group(1))
        if num: return f"{num}/?"
    return span_text

def normalize_ordinal(span_text):
    s=span_text.lower().strip()
    if s in ORDINAL_WORDS: return str(ORDINAL_WORDS[s])
    m=re.search(r"(?:hạng|thứ)\s+(.+)", s)
    if m:
        k=m.group(1).strip()
        if k in ORDINAL_WORDS: return f"{m.group(0).split()[0]} {ORDINAL_WORDS[k]}"
        nv=vietnamese_to_number(k)
        if nv is not None: return f"{m.group(0).split()[0]} {nv}"
    return span_text

# normalization dispatcher
_NORMALIZER = {
    "date": normalize_date,
    "time": normalize_time,
    "currency": normalize_currency,
    "percentage": normalize_percentage,
    "phone/account": normalize_phone,
    "number_sequence": normalize_number_sequence,
    "decimal": normalize_decimal,
    "fraction": normalize_fraction,
    "ordinal": normalize_ordinal,
    "year_duration": lambda s: re.sub(r"(cách đây\s+)(" + NUM_SEQ + r")(\s+năm)", lambda m: m.group(1) + (str(vietnamese_to_number(m.group(2)) if vietnamese_to_number(m.group(2)) is not None else m.group(2))) + m.group(3), s, flags=re.I)
}


def process_sentence(sentence):
    ents = detect_number_entities(sentence)
    enriched = []

    for e in ents:
        case = e["case"]
        text_span = e["text"]

        norm_fn = _NORMALIZER.get(case)
        if norm_fn:
            try:
                norm = norm_fn(text_span)
            except Exception:
                norm = text_span
        else:
            tmp = vietnamese_to_number(text_span)
            norm = str(tmp) if tmp is not None else text_span

        enriched.append({
            "text": text_span,
            "case": case,
            "start": e["start"],
            "end": e["end"],
            "normalized": norm,
        })

    return enriched, normalize_detected_entities(sentence, enriched)



# reuse detect & normalize functions from above
def detect_number_entities(text):
    return detect_number_entities__impl(text)


def filter_short_number_sequences(entities, text, min_tokens=3):
    """
    Bỏ qua các number_sequence có ít hơn min_tokens token.
    Mặc định min_tokens=3 để tránh postprocess các cụm ngắn như 'một hai', 'ba bốn'.
    """
    filtered = []
    for e in entities:
        if e["case"] == "number_sequence":
            num_tokens = len(e["text"].split())
            if num_tokens < min_tokens:
                continue
        filtered.append(e)
    return filtered


def detect_number_entities__impl(text):
    if not text:
        return []
    txt = text.strip()
    results = []
    occupied = []

    for pe in predetect_specials(txt):
        results.append(pe)
        occupied.append((pe["start"], pe["end"]))

    for case, pattern in _PATTERNS:
        for m in pattern.finditer(txt):
            s, e = m.span()
            if _overlaps(occupied, s, e):
                continue
            results.append({"text": m.group().strip(), "case": case, "start": s, "end": e})
            occupied.append((s, e))

    results.sort(key=lambda x: x["start"])
    merged = merge_adjacent_entities(results, txt)
    return filter_short_number_sequences(merged, txt, min_tokens=3)


def normalize_detected_entities(text, detected_entities):
    if not detected_entities:
        return text
    txt = text
    ents = sorted(detected_entities, key=lambda x: x["start"])
    out_parts=[]; last=0
    for ent in ents:
        s,e=ent["start"], ent["end"]
        out_parts.append(txt[last:s])
        span=ent["text"]; case=ent["case"]
        norm = _NORMALIZER.get(case, lambda s: s)(span) if case in _NORMALIZER else (str(vietnamese_words_to_int(span)) if vietnamese_words_to_int(span) is not None else span)
        out_parts.append(norm)
        last=e
    out_parts.append(txt[last:])
    return "".join(out_parts)



# cấu hình
MIN_TOKENS_FOR_NORMALIZE = 3

# helper: đếm token số thực sự trong span (bỏ dấu câu)
def _count_number_tokens(span_text):
    tokens = re.findall(r"\b\w+\b", span_text.lower())
    # coi là token số nếu là chữ số hay là từ số trong danh sách NUM_WORDS_SIMPLE/VI_NUM_MAP
    cnt = 0
    for t in tokens:
        if re.fullmatch(r"\d+", t) or t in NUM_WORDS_SIMPLE or t in PHONE_DIGIT_WORDS:
            cnt += 1
    return cnt

def normalize_detected_entities(text, detected_entities):
    """
    Replace detected entities left->right, nhưng bỏ qua normalize cho
    number_sequence có token < MIN_TOKENS_FOR_NORMALIZE.
    """
    if not detected_entities:
        return text

    txt = text
    ents = sorted(detected_entities, key=lambda x: x["start"])
    out_parts = []
    last = 0

    for ent in ents:
        s, e = ent["start"], ent["end"]
        # giữ phần trước entity
        out_parts.append(txt[last:s])

        span = ent["text"]
        case = ent["case"]

        # Nếu là number_sequence, kiểm tra số token number-like
        if case == "number_sequence":
            num_tokens = _count_number_tokens(span)
            if num_tokens < MIN_TOKENS_FOR_NORMALIZE:
                # không normalize -> giữ nguyên span
                out_parts.append(span)
                last = e
                continue

        # Nếu là phone/account: có thể áp dụng heuristics khác (giữ nếu quá ngắn)
        if case == "phone/account":
            num_tokens = _count_number_tokens(span)
            # phone/account thường cần ít nhất 3-4 token để thực sự là phone, 
            # điều chỉnh nếu cần
            if num_tokens < 3:
                out_parts.append(span)
                last = e
                continue

        # bình thường gọi normalizer
        norm_fn = _NORMALIZER.get(case, None)
        if norm_fn:
            try:
                norm = norm_fn(span)
            except Exception:
                norm = span
        else:
            tmp = vietnamese_to_number(span)
            norm = str(tmp) if tmp is not None else span

        out_parts.append(norm)
        last = e

    out_parts.append(txt[last:])
    return "".join(out_parts)

