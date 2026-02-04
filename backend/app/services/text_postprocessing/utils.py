import re
import chardet
from app.core.config import settings

def load_vn_unigram_vocab(path):
    """
    Đọc file dictionary, xử lý mọi loại encoding
    và trả về set từ đơn.
    """
    # Đọc nhị phân để dò encoding
    with open(path, "rb") as f:
        raw = f.read()

    detected = chardet.detect(raw)
    enc = detected["encoding"] or "utf-8"

    text = raw.decode(enc, errors="replace")
    vocab = set()

    for line in text.splitlines():
        line = line.strip().lower()
        if not line:
            continue

        # Tách từ tiếng Việt (có dấu)
        words = re.findall(r"[a-zA-ZÀ-ỹđĐ]+", line)
        for w in words:
            vocab.add(w)

    return vocab


vn_unigram_vocab = load_vn_unigram_vocab(settings.VN_UNIGRAM_VOCAB_PATH)


def is_vietnamese_word(w):
    w = w.strip()
    w = w.lower()
    return w in vn_unigram_vocab


import nltk
from nltk.corpus import words

# tải 1 lần
nltk.download("words", quiet=True)
EN_WORDS = set(words.words())

def is_english_word(w):
    return w.lower() in EN_WORDS
