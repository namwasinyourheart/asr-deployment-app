import re
import string

def _preserve_case(orig: str, repl: str) -> str:
    """
    Preserve casing from orig to repl:
    - if orig is all upper -> repl.upper()
    - elif orig is title-like (first char upper) -> Title Case for repl
    - elif orig is all lower -> repl.lower()
    - else -> return repl as-is
    """
    if orig.isupper():
        return repl.upper()
    # treat as title if first character or any first char of word is upper
    if any(w and w[0].isupper() for w in re.findall(r"\w+", orig)):
        # title-case replacement (capitalize each word)
        return " ".join([w.capitalize() for w in repl.split()])
    if orig.islower():
        return repl.lower()
    return repl


def postprocess_sec_simple(
    text: str,
    vocab_map: dict,
    case_sensitive: bool = False,
    word_boundary: bool = True,
    preserve_case: bool = True,
) -> str:
    """
    Replace substrings from text using vocab_map (sai -> đúng) WITHOUT tokenizing.
    - vocab_map keys and values are strings.
    - case_sensitive: if False, matching is case-insensitive.
    - word_boundary: if True, require word boundaries around matches (\b). For multi-word keys
                     this still works; if False, do raw substring matching.
    - preserve_case: try to preserve capitalization pattern from matched substring to replacement.

    Example:
        vocab_map = {"Nam Tử Liêm": "Nam Từ Liêm", "diên việt vốt spanh": "Liên Việt Postbank"}
        postprocess_sec_simple("huyện Nam Tử Liêm", vocab_map) -> "huyện Nam Từ Liêm"
    """
    if not text or not vocab_map:
        return text

    # prepare mapping keys; sort by length desc to prefer longest match first
    keys = sorted(vocab_map.keys(), key=lambda k: len(k), reverse=True)
    # escape keys for regex
    escaped_keys = [re.escape(k) for k in keys]

    # build pattern
    if word_boundary:
        # use \b, good for most cases (unicode words ok in Python)
        pattern = r"\b(?:" + "|".join(escaped_keys) + r")\b"
    else:
        pattern = r"(?: " + "|".join(escaped_keys) + r")" if False else r"(?:%s)" % "|".join(escaped_keys)

    flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(pattern, flags)

    # make lowercase mapping if case-insensitive for lookup
    if not case_sensitive:
        lowered_map = {k.lower(): v for k, v in vocab_map.items()}

    def _repl(m: re.Match) -> str:
        matched = m.group(0)
        # determine canonical key in vocab_map
        if case_sensitive:
            key = matched
            repl = vocab_map.get(key)
        else:
            key = matched.lower()
            repl = lowered_map.get(key)

        if repl is None:
            # fallback (shouldn't happen if keys covered)
            return matched

        if preserve_case:
            return _preserve_case(matched, repl)
        return repl

    result = regex.sub(_repl, text)
    return result
