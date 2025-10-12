import sys
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("BASE_DIR", BASE_DIR)

# backend directory
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

sys.path.append(BACKEND_DIR)

from app.services.postprocessing.postprocess import postprocess_number


import random


def number_to_vietnamese(n, zero_read="lẻ"):
    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    tens_words = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi",
                  "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]
    scales = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ", "tỷ tỷ"]

    def read_three_digits(num, is_first_group=False):
        hundred = num // 100
        ten = (num % 100) // 10
        one = num % 10
        result = []

        # Hàng trăm
        if hundred > 0:
            result.append(units[hundred] + " trăm")
        elif not is_first_group and num != 0:
            result.append("không trăm")

        # Hàng chục
        if ten > 1:
            result.append(tens_words[ten])
        elif ten == 1:
            result.append("mười")
        elif ten == 0 and one > 0 and (hundred > 0 or not is_first_group):
            result.append(zero_read)

        # Hàng đơn vị
        if one > 0:
            if ten == 0 or ten == 1:
                if one == 5 and ten > 0:
                    result.append("lăm")
                else:
                    result.append(units[one])
            else:
                if one == 1:
                    result.append("mốt")
                elif one == 4:
                    result.append("tư")
                elif one == 5:
                    result.append("lăm")
                else:
                    result.append(units[one])

        return " ".join(result)

    if n == 0:
        return "không"

    # Chia số thành các nhóm 3 chữ số
    str_n = str(n)
    groups = []
    while str_n:
        groups.insert(0, int(str_n[-3:]))
        str_n = str_n[:-3]

    words = []
    group_len = len(groups)
    for idx, g in enumerate(groups):
        is_first_group = (idx == 0)
        # Nếu nhóm ≠ 0 hoặc nằm giữa các nhóm còn số khác thì mới đọc
        has_nonzero_after = any(groups[idx + 1:]) if idx + 1 < group_len else False
        if g != 0 or has_nonzero_after:
            group_words = read_three_digits(g, is_first_group)
            if group_words:
                words.append(group_words)
            scale = scales[group_len - idx - 1]
            if scale and (g != 0 or has_nonzero_after):
                words.append(scale)

    return " ".join(words).strip()


def generate_test_cases(d, samples=None):
    """
    Sinh số đại diện cho số có d chữ số theo quy luật 2^(d-1).
    samples: list các chữ số ≠0 để random, mặc định [1..9]
    """
    if samples is None:
        samples = list(range(1, 10))

    results = []
    first_digit = random.choice(samples)  # chữ số đầu luôn ≠0

    # Sinh tất cả 2^(d-1) pattern cho các chữ số còn lại
    for mask in range(2**(d-1)):
        digits = [first_digit]
        for pos in range(d-1):
            if (mask >> pos) & 1:
                digits.append(random.choice(samples))  # ≠0
            else:
                digits.append(0)
        n = int("".join(str(x) for x in digits))
        results.append(n)

    return results


def generate_test_dataset(max_digits=6):
    dataset = []
    for d in range(1, max_digits+1):
        numbers = generate_test_cases(d)
        for n in numbers:
            dataset.append((n, number_to_vietnamese(n)))
    return dataset


# # Demo
# if __name__ == "__main__":
#     dataset = generate_test_dataset(max_digits=6)
#     for n, vn in dataset:
#         print(f"{n} -> {vn}")



if __name__ == "__main__":
    
    asr_number_sequences_texts = [
        "hai trăm linh năm hai trăm linh bảy", 
        "ba trăm nghìn",
        "ba trăm nghìn không trăm ba mươi hai",
        "ba trăm năm mươi hai nghìn bốn trăm sáu mươi hai",
        # "5 triệu đồng",
        "ba mươi tám nghìn hai trăm ba mươi tư",
        "hai trăm nghìn không trăm lẻ bốn",
        "một trăm ngàn",
        "mười nghìn không trăm lẻ bảy",
        "mười nghìn không trăm mười lăm",
        "mười nghìn hai trăm hai mươi sáu",
        "một triệu hai trăm ngàn ba mươi",
        "một triệu sáu trăm lẻ bảy",
        "một ngàn hai trăm năm mươi",
        "một ngàn lẻ bốn",
        "một ngàn không trăm lẻ bốn",
        "một trăm linh bảy",
        "một trăm ba mươi hai",
        "một trăm",
        "hai trăm ninh hai ngàn ba trăm hai mưoi mốt",
        "hai trăm năm mươi",
        "năm mươi triệu hai trăm ngàn",
        "năm mươi triệu hai trăm nghìn",
        "một trăm hai mươi ngàn ba trăm"
    ]

    asr_currency_texts = [
        "2 trăm chiếc",
        "2 trăm đô la",
        "200 USD",

        "2 nghìn đồng",
        "2000 đồng",

        "2 triệu đồng",
        "2000000 đồng",

        "5 triệu đồng",
        "5000000 đồng",

        "2 tỷ đồng",   
        "2000000000 đồng",
        "hai tỷ đồng",
    ]


    tests = [
        "lương ba trăm triệu một năm hai mươi triệu một tháng",
        "lương chín triệu một năm và 20 triệu một tháng",
        "hai trăm ninh hai",
        "Không thở ơ quá và cũng không quan tâm quá trong một thời điểm",
        "không quan tâm quá trong một thời điểm",
        "hai trăm linh năm",
        "không chín bảy bảy bốn không tám bốn hai không",
        "hai trăm linh năm và ba trăm linh bảy",
        "hai trăm linh năm hai trăm linh bảy",
        "một trăm ba mươi hai một trăm linh bảy",
        "mười ba mười lăm",
        "năm bảy",
        "năm mươi triệu hai trăm ngàn",
        "5 triệu đồng",

    ]

    for t in tests:
        output = postprocess_number(t)
        print(f"{t} -> {output}")



    # asr_currency_texts = []
    # dataset = generate_test_dataset(max_digits=6)
    # for n, vn in dataset:
    #     # print(f"{n} -> {vn}")

    #     vn_currency = vn + " đồng"
    #     # print(f"{n} -> {vn_currency}")
    #     # asr_currency_texts.append(vn_currency)

    #     output = postprocess_number(vn_currency)
    #     print(f"{n} -> {vn_currency} -> {output}")


    # for text in asr_number_sequences_texts:
    #     output = postprocess_number(text)
    #     print(f"{text} -> {output}")


    # for text in asr_currency_texts:
    #     output = postprocess_number(text)
    #     print(f"{text} -> {output}")