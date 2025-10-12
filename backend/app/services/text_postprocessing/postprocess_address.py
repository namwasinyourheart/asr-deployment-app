import re
from typing import List

def replace_words_with_slash(text: str, keywords: List[str] = None) -> str:
    """
    Detect and convert number sequences containing specific keywords into
    slash-separated format.

    Example:
        "15 Trên 6 Trên 89"  -> "15/6/89"
        "15 gạch chéo 6 sẹc 89" -> "15/6/89"

    Args:
        text (str): Input address string
        keywords (List[str]): List of words/phrases to replace with "/"
                              Default = ["Trên", "gạch chéo", "sẹc", "sạch"]

    Notes:
        - Only affects cases where keyword is between digits.
        - Keeps keywords outside of number sequences unchanged.
    """
    if keywords is None:
        keywords = [
            "trên", 
            "gạch chéo", 
            "sẹc", 
            "sạch", 
            "xuyệt", 
            "sạc",
            "xẹt",
            "sẹt",
            "xeạc"
        ]

    # join all keywords into one regex alternation
    joined = "|".join(re.escape(k) for k in keywords)
    # pattern = re.compile(rf'\d+(?:\s+(?:{joined})\s+\d+)+', flags=re.IGNORECASE)

    pattern = re.compile(rf'[0-9A-Za-z]+(?:\s+(?:{joined})\s+[0-9A-Za-z]+)+',
                         flags=re.IGNORECASE)

    def repl(match: re.Match) -> str:
        seq = match.group(0)
        return re.sub(rf'\s*(?:{joined})\s*', '/', seq, flags=re.IGNORECASE)

    return pattern.sub(repl, text)

import re
from typing import List

def replace_words_with_dash(text: str, keywords: List[str] = None) -> str:
    """
    Detect and convert number sequences containing dash-like keywords
    into dash-separated format.

    Example:
        "113 gạch ngang 115" -> "113-115"
        "200 ngang 202" -> "200-202"

    Args:
        text (str): Input address string
        keywords (List[str]): List of words/phrases to replace with "-"
                              Default = ["gạch ngang", "ngang"]

    Notes:
        - Only affects cases where keyword is between digits.
        - Keeps keywords outside of number sequences unchanged.
    """
    if keywords is None:
        keywords = ["gạch ngang", "ngang"]

    joined = "|".join(re.escape(k) for k in keywords)
    pattern = re.compile(rf'\d+(?:\s+(?:{joined})\s+\d+)+', flags=re.IGNORECASE)

    def repl(match: re.Match) -> str:
        seq = match.group(0)
        return re.sub(rf'\s*(?:{joined})\s*', '-', seq, flags=re.IGNORECASE)

    return pattern.sub(repl, text)



if __name__ == "__main__":
    # --- Quick test ---
    examples = [
        "15 sẹc 6 trên 8 và 22 trên 11  gạch chéo 34 sẹc 5 Đường XYZ",
        "15 Trên 6 Trên 89 Tô Ngọc Vân, Quận 12",
        "Nhà tôi nằm Trên đường lớn, số 15 Trên 6 Trên 89 Quận 12",
        "7 Trên 2 Nguyễn Thái Học, Quận 1",
        "Không có chữ Trên trong số liệu này",
        "5 Trên 3 Trên 2 Trên 1 Khu phố 9",
        "15 Trên 6 Trên 8 và 22 Trên 34 Trên 8 Trên 9 XYZ",
    ]

    for ex in examples:
        print(ex)
        print(" ->", replace_words_with_slash(ex))
    


    # --- Quick test ---
    examples = [
        "số nhà 113 gạch ngang 115 đường Lê Văn Sỹ",
        "200 ngang 202 phường 5, quận 3",
        "123 GẠCH NGANG 125 Nguyễn Huệ",
        "Không có gạch ngang ở đây",
    ]

    for ex in examples:
        print(ex)
        print(" ->", replace_words_with_dash(ex))
