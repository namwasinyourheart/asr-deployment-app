from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.text_postprocessing.utils import is_english_word, is_vietnamese_word

router = APIRouter(tags=["language"])
logger = logging.getLogger(__name__)

class WordCheckRequest(BaseModel):
    word: str

class WordCheckResponse(BaseModel):
    is_valid: bool
    word: str

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

@router.get("/is_vietnamese_word", response_model=WordCheckResponse)
async def check_vietnamese_word(word: str):
    """
    Check if a word is a valid Vietnamese word.
    
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
            "is_valid": is_vietnamese_word(word),
            "word": word
        }
    except Exception as e:
        logger.error(f"Error checking Vietnamese word: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing request")
