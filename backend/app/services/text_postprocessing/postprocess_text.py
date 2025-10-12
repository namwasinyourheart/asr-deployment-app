import sys
import os
# Thêm thư mục gốc vào PYTHONPATH
# print(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from .postprocess_number import process_sentence
from .postprocess_address import replace_words_with_slash, replace_words_with_dash


def postprocess_address(text: str) -> str:
    text = replace_words_with_dash(text.strip())
    text = replace_words_with_slash(text.strip())
    return text

def postprocess_number(asr_text: str) -> str:
    """
    Nhận input là ASR text (Vietnamese) và trả về text đã được chuẩn hóa
    các số, bao gồm: phone/account, number_sequence, currency, percentage, fraction, ordinal, decimal, date, time, year_duration.
    """
    enriched, normalized_sentence = process_sentence(asr_text.strip())
    return normalized_sentence


