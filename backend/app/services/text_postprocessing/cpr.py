# app/services/postprocess_cpr.py

def postprocess_cpr(text: str, cpr_model) -> str:
    """
    Nhận input text, trả về text đã được phục hồi viết hoa và dấu câu.
    """
    text = cpr_model(text)

    if isinstance(text, list):
        text = text[0]
    
    return text
