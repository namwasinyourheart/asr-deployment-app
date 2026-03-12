from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from typing import Dict

import logging

from app.services.text_postprocessing.utils import is_english_word, is_vietnamese_word, is_vietnamese_word_batch

router = APIRouter(tags=["language"])
logger = logging.getLogger(__name__)

class WordCheckRequest(BaseModel):
    word: str

class WordCheckResponse(BaseModel):
    is_valid: bool
    word: str

from typing import List, Union
from pydantic import BaseModel

class WordCheckRequest(BaseModel):
    words: Union[str, List[str]]


class WordCheckBatchResponse(BaseModel):
    results: Dict[str, bool]

@router.get("/is_english_word", response_model=WordCheckResponse)
async def check_english_word(word: str):
    """
    Check if a word is a valid English word.
    
    Args:
        word: The word to check
        
    Returns:
        dict: {
            "is_valid": bool,
            "word": str
        }
    """
    try:
        return {
            "is_valid": is_english_word(word),
            "word": word
        }
    except Exception as e:
        logger.error(f"Error checking English word: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing request")

# @router.get("/is_vietnamese_word", response_model=WordCheckResponse)
# async def check_vietnamese_word(word: str):
#     """
#     Check if a word is a valid Vietnamese word.
    
#     Args:
#         word: The word to check
        
#     Returns:
#         dict: {
#             "is_valid": bool,
#             "word": str
#         }
#     """
#     try:
#         return {
#             "is_valid": is_vietnamese_word(word),
#             "word": word
#         }
#     except Exception as e:
#         logger.error(f"Error checking Vietnamese word: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error processing request")

# @router.get("/is_vietnamese_word_batch", response_model=WordCheckResponse)
# async def check_vietnamese_word_batch(words: List[str]):
#     """
#     Check if a word is a valid Vietnamese word.
    
#     Args:
#         word: The word to check
        
#     Returns:
#         dict: {str: bool}
#     """
#     try:
#         return is_vietnamese_word_batch(words)
#     except Exception as e:
#         logger.error(f"Error checking Vietnamese word: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error processing request")


@router.post(
    "/is_vietnamese_word",
    response_model=WordCheckBatchResponse
)
async def check_vietnamese_word(req: WordCheckRequest):
    """
    Check Vietnamese word(s).
    Accepts:
    - single word (string)
    - batch words (list of strings)
    """
    try:
        if isinstance(req.words, str):
            words = [req.words]
        else:
            words = req.words

        # results = {
        #     w: is_vietnamese_word(w)
        #     for w in words
        # }

        batch_results = is_vietnamese_word_batch(words)
        return {"results": batch_results}

    except Exception as e:
        logger.error(f"Error checking Vietnamese word: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error processing request"
        )


# curl -X POST "http://localhost:8000/is_vietnamese_word" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "words": "chào"
#   }'

