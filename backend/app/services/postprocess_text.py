import sys
import os

sys.path.append(os.path.dirname(__file__))

from text_postprocessing.postprocess_text import postprocess_number, postprocess_address  
from text_postprocessing.postprocess_cpr import postprocess_cpr
from text_postprocessing.postprocess_sec import postprocess_sec_simple as postprocess_sec



def load_sec_dict(file_path: str):
    sec_dict = {}

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "->" not in line:
                continue
            wrong, correct = line.split("->", 1)
            wrong = wrong.strip()
            correct = correct.strip()
            sec_dict[wrong] = correct
    return sec_dict



def postprocess_text(text: str, sec_dict: dict, cpr_model) -> str:
    """
    Receive input ASR text (Vietnamese) and return the text that has been standardized
    for numbers, including: phone/account, number_sequence, currency, percentage, fraction, ordinal, decimal, date, time, year_duration.
    """


    text = postprocess_number(text)
    print("postprocess_number ->", text)


    text = postprocess_address(text)
    print("postprocess_address ->", text)


    text = postprocess_sec(text, sec_dict)
    print("postprocess_sec ->", text)

    text = postprocess_cpr(text, cpr_model)
    print("postprocess_cpr ->", text)

    return {"text": text}
