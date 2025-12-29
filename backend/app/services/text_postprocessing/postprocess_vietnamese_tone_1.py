#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================
#  BẢNG NGUYÊN ÂM / DẤU
# ==============================
bang_nguyen_am = [
    ['a', 'à', 'á', 'ả', 'ã', 'ạ', 'a'],
    ['ă', 'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ', 'aw'],
    ['â', 'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ', 'aa'],
    ['e', 'è', 'é', 'ẻ', 'ẽ', 'ẹ', 'e'],
    ['ê', 'ề', 'ế', 'ể', 'ễ', 'ệ', 'ee'],
    ['i', 'ì', 'í', 'ỉ', 'ĩ', 'ị', 'i'],
    ['o', 'ò', 'ó', 'ỏ', 'õ', 'ọ', 'o'],
    ['ô', 'ồ', 'ố', 'ổ', 'ỗ', 'ộ', 'oo'],
    ['ơ', 'ờ', 'ớ', 'ở', 'ỡ', 'ợ', 'ow'],
    ['u', 'ù', 'ú', 'ủ', 'ũ', 'ụ', 'u'],
    ['ư', 'ừ', 'ứ', 'ử', 'ữ', 'ự', 'uw'],
    ['y', 'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ', 'y']
]

bang_ky_tu_dau = ['', 'f', 's', 'r', 'x', 'j']

# ==============================
#  TẠO MAP NGUYÊN ÂM (CẢ HOA + THƯỜNG)
# ==============================
nguyen_am_to_ids = {}
for i in range(len(bang_nguyen_am)):
    for j in range(6):  # 0 → 5
        base = bang_nguyen_am[i][j]
        nguyen_am_to_ids[base] = (i, j)
        nguyen_am_to_ids[base.upper()] = (i, j)


# ==============================
#  VALIDATION
# ==============================
def is_valid_vietnam_word(word):
    chars = list(word)
    last_idx = -1
    for idx, ch in enumerate(chars):
        x, y = nguyen_am_to_ids.get(ch, (-1, -1))
        if x != -1:
            if last_idx == -1:
                last_idx = idx
            else:
                if idx - last_idx != 1:
                    return False
                last_idx = idx
    return True


# ==============================
#  CHUẨN HÓA DẤU CHO MỘT TỪ
# ==============================
def chuan_hoa_dau_tu_tieng_viet(word):
    if not is_valid_vietnam_word(word):
        return word

    chars = list(word)
    dau_cau = 0
    nguyen_am_index = []
    qu_or_gi = False

    for idx, ch in enumerate(chars):
        x, y = nguyen_am_to_ids.get(ch, (-1, -1))
        if x == -1:
            continue

        # detect "qu"
        if x == 9 and idx > 0 and chars[idx - 1].lower() == 'q':
            chars[idx] = 'U' if ch.isupper() else 'u'
            qu_or_gi = True

        # detect "gi"
        elif x == 5 and idx > 0 and chars[idx - 1].lower() == 'g':
            chars[idx] = 'I' if ch.isupper() else 'i'
            qu_or_gi = True

        # remove tone mark
        if y != 0:
            dau_cau = y
            base = bang_nguyen_am[x][0]
            chars[idx] = base.upper() if ch.isupper() else base

        if not (qu_or_gi and idx == 1):
            nguyen_am_index.append(idx)

    # ------------------
    # word with only 1 vowel
    # ------------------
    if len(nguyen_am_index) < 2:
        if qu_or_gi:
            if len(chars) == 2:
                x, y = nguyen_am_to_ids[chars[1]]
                t = bang_nguyen_am[x][dau_cau]
                chars[1] = t.upper() if chars[1].isupper() else t
            else:
                x, y = nguyen_am_to_ids.get(chars[2], (-1, -1))
                if x != -1:
                    t = bang_nguyen_am[x][dau_cau]
                    chars[2] = t.upper() if chars[2].isupper() else t
                else:
                    cand = bang_nguyen_am[5][dau_cau] if chars[1].lower() == 'i' else bang_nguyen_am[9][dau_cau]
                    chars[1] = cand.upper() if chars[1].isupper() else cand
            return ''.join(chars)
        return word

    # ------------------
    # ê, ơ ưu tiên nhận dấu
    # ------------------
    for idx in nguyen_am_index:
        x, _ = nguyen_am_to_ids[chars[idx]]
        if x in (4, 8):  # ê, ơ
            t = bang_nguyen_am[x][dau_cau]
            chars[idx] = t.upper() if chars[idx].isupper() else t
            return ''.join(chars)

    # ------------------
    # 2 vowel cluster
    # ------------------
    if len(nguyen_am_index) == 2:
        first, last = nguyen_am_index
        if last == len(chars) - 1:
            x, _ = nguyen_am_to_ids[chars[first]]
            t = bang_nguyen_am[x][dau_cau]
            chars[first] = t.upper() if chars[first].isupper() else t
        else:
            x, _ = nguyen_am_to_ids[chars[last]]
            t = bang_nguyen_am[x][dau_cau]
            chars[last] = t.upper() if chars[last].isupper() else t

    else:
        mid = nguyen_am_index[1]
        x, _ = nguyen_am_to_ids[chars[mid]]
        t = bang_nguyen_am[x][dau_cau]
        chars[mid] = t.upper() if chars[mid].isupper() else t

    return ''.join(chars)


# ==============================
#  CHUẨN HÓA CẢ CÂU
# ==============================
# def normalize_vietnamese_tone(sentence):
    
#     words = sentence.split()
#     return " ".join(chuan_hoa_dau_tu_tieng_viet(w) for w in words)

import regex as re

def normalize_vietnamese_tone(sentence):
    def norm_word(w):
        m = re.match(r"^([\p{L}]+)(.*)$", w)
        if not m:
            return w
        core, suffix = m.groups()
        return chuan_hoa_dau_tu_tieng_viet(core) + suffix

    words = sentence.split()
    return " ".join(norm_word(w) for w in words)



# ==============================
#  DEMO TEST
# ==============================
if __name__ == "__main__":

    print(is_valid_vietnam_word("mẫp"))
    tests = [
        # "Quỳ qùy hòa Hoà",
        # "Xóm Hoà Qùy",
        # "hòa Hoà",
        # "toi yeu tieng Viet",
        # "giàu có", 
        # "Quảng cáo GIÀU",
        "Thôn Trung Hà, Xã Thái Hoà, Huyện Ba Vì, Thành phố Hà Nội",
    ]

    for t in tests:
        print("input :", t)
        print("output:", normalize_vietnamese_tone(t))
        print("---")
