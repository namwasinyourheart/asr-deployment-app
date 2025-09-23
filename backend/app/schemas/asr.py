from pydantic import BaseModel
from typing import List, Optional, Any

class ASRResponse(BaseModel):
    text: str
    duration: Optional[float] = None   # audio duration
    processing_time: Optional[float] = None  # tổng thời gian xử lý pipeline
