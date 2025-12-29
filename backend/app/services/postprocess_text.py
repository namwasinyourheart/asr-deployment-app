import sys
import os

sys.path.append(os.path.dirname(__file__))

from text_postprocessing.number import postprocess_number
from text_postprocessing.address import postprocess_address
from text_postprocessing.cpr import postprocess_cpr
from text_postprocessing.sec import postprocess_sec_simple as postprocess_sec
from text_postprocessing.postprocess_vietnamese_tone import normalize_vietnamese_tone

from app.core.config import settings
from .service_utils import setup_logger

logger = setup_logger(__name__)

_sec_dict = None
_cpr_model = None

CPR_MODEL_PATH = settings.CPR_MODEL_PATH
CPR_VOCAB_PATH = os.path.join(CPR_MODEL_PATH, "vocabulary")
sys.path.append(os.path.join(CPR_MODEL_PATH))


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


def _ensure_sec_model():

    global _sec_dict

    if _sec_dict is None:
        logger.info("Loading SEC model...")
        sec_dict_path = os.path.join(settings.SEC_MODEL_PATH, "sec_dict.txt")
        _sec_dict = load_sec_dict(sec_dict_path)

def _load_cpr_model():
    logger.info("Loading CPR model...")
    from gec_model import GecBERTModel
    model = GecBERTModel(
        vocab_path=CPR_VOCAB_PATH,
        model_paths=CPR_MODEL_PATH,
        split_chunk=True
    )
    return model

def _ensure_cpr_model():
    global _cpr_model
    if _cpr_model is None:  
        _cpr_model = _load_cpr_model()


_ensure_sec_model()
_ensure_cpr_model()

def postprocess_text(
    text: str, 
    sec_dict: dict=_sec_dict, 
    cpr_model=_cpr_model
) -> str:
    """
    Receive input ASR text (Vietnamese) and return the text that has been standardized
    for numbers, including: phone/account, number_sequence, currency, percentage, fraction, ordinal, decimal, date, time, year_duration.
    """

    logger.info("Starting postprocess transcript...")
    logger.info("Raw transcript: %s", text)

    text = postprocess_number(text)
    logger.info("Numbers Reformatting: %s", text)
  
    text = postprocess_address(text)
    logger.info("Address Error Correction: %s", text)

    text = postprocess_sec(text, sec_dict)
    logger.info("Spelling Error Correction: %s", text)

    text = normalize_vietnamese_tone(text)
    logger.info("Tone Normalization: %s", text)

    text = postprocess_cpr(text, cpr_model)
    logger.info("Capitalization and Punctuation Restoration: %s", text)
    return {"text": text}


def cpr(
    text: str,
    cpr_model=_cpr_model
) -> str:
    text = postprocess_cpr(text, cpr_model)

    return {"text": text}