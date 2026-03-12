import re
# import chardet
from app.core.config import settings
from typing import List

# def load_vn_unigram_vocab(path):
#     """
#     Đọc file dictionary, xử lý mọi loại encoding
#     và trả về set từ đơn.
#     """
#     # Đọc nhị phân để dò encoding
#     with open(path, "rb") as f:
#         raw = f.read()

#     detected = chardet.detect(raw)
#     enc = detected["encoding"] or "utf-8"

#     text = raw.decode(enc, errors="replace")
#     vocab = set()

#     for line in text.splitlines():
#         line = line.strip().lower()
#         if not line:
#             continue

#         # Tách từ tiếng Việt (có dấu)
#         words = re.findall(r"[a-zA-ZÀ-ỹđĐ]+", line)
#         for w in words:
#             vocab.add(w)

#     return vocab
def load_vn_unigram_vocab(path):
    """
    Đọc file dictionary (utf-8)
    và trả về set từ đơn.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

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


def is_vietnamese_word(word: str):
    word = word.strip()
    word = word.lower()
    return word in vn_unigram_vocab


def is_vietnamese_word_batch(words: List[str]):
    normalized = {w.strip().lower() for w in words}
    vi_words = normalized & vn_unigram_vocab

    return {
        w: w.strip().lower() in vi_words
        for w in words
    }



import nltk
from nltk.corpus import words

# tải 1 lần
nltk.download("words", quiet=True)
EN_WORDS = set(words.words())

def is_english_word(word: str):
    return word.lower() in EN_WORDS
