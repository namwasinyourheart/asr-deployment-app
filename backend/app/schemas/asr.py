from pydantic import BaseModel
from typing import List, Optional, Any

class ASRResponse(BaseModel):
    text: str
    duration: Optional[float] = None  
    total_processing_time: Optional[float] = None 
    speech_enhancement_time: Optional[float] = None 
    asr_time: Optional[float] = None  
    text_postprocessing_time: Optional[float] = None 
    


class ASRRequest(BaseModel):
    enhance_speech: bool = True
    postprocess_text: bool = True
