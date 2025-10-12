
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Load model once
tokenizer = AutoTokenizer.from_pretrained("NlpHUST/ner-vietnamese-electra-base")
model = AutoModelForTokenClassification.from_pretrained("NlpHUST/ner-vietnamese-electra-base")
nlp_ner = pipeline("ner", model=model, tokenizer=tokenizer)

def capitalize_entity(text: str) -> str:
    """Viết hoa chữ cái đầu của một cụm từ, giữ nguyên các từ khác."""
    return ' '.join(w.capitalize() for w in text.split())

def postprocess_uppercase(text: str, nlp_ner) -> str:
    """
    Nhận input text, thực hiện NER, viết hoa chữ cái đầu các entity: PERSON và LOCATION.
    Trả về text đã được postprocess.
    """
    ner_results = nlp_ner(text)

    if not ner_results:
        return text

    # Gộp các token liên tiếp cùng entity (B/I)
    merged_entities = []
    current = None
    for ent in ner_results:
        if ent['entity'].startswith("B-"):
            if current:
                merged_entities.append(current)
            current = {
                "start": ent['start'],
                "end": ent['end'],
                "entity": ent['entity'][2:],
                "text": ent['word']
            }
        elif ent['entity'].startswith("I-") and current and current['entity'] == ent['entity'][2:]:
            # nối token tiếp
            current['end'] = ent['end']
            current['text'] += ' ' + ent['word']
        else:
            if current:
                merged_entities.append(current)
            current = None
    if current:
        merged_entities.append(current)

    # Tạo text postprocess
    out_parts = []
    last_idx = 0
    for ent in merged_entities:
        out_parts.append(text[last_idx:ent['start']])
        if ent['entity'] in ('PERSON', 'LOCATION', 'ORGANIZATION'):
            out_parts.append(capitalize_entity(ent['text']))
        else:
            out_parts.append(ent['text'])
        last_idx = ent['end']
    out_parts.append(text[last_idx:])

    return ''.join(out_parts)
