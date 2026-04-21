import re
import sys

# Ported from scripts/checks/ukrainian.py (with the diff applied)
RUSSICISMS = {"самий": "найкращий"}

FALSE_POSITIVE_PATTERNS = {
    "самий": re.compile(
        r"(?:той|та|те|ті|тій|того|тому|тих|тими|тією|тої)\s+сам(?:ий|а|е|і|ого|ому|их|ими|ій|ою|ої)",
        re.IGNORECASE,
    ),
}

def check(content):
    content_lower = content.lower()
    for russian, fix in RUSSICISMS.items():
        # Word boundary: surrounded by non-Cyrillic characters
        pattern = rf"(?<![а-яґєіїА-ЯҐЄІЇ']){re.escape(russian.lower())}(?![а-яґєіїА-ЯҐЄІЇ'])"
        matches = re.findall(pattern, content_lower)
        if matches:
            fp_pattern = FALSE_POSITIVE_PATTERNS.get(russian)
            if fp_pattern:
                false_positives = len(fp_pattern.findall(content_lower))
                print(f"DEBUG: '{russian}' matches: {len(matches)} | false_positives ('{fp_pattern.pattern}'): {false_positives}")
                real_count = len(matches) - false_positives
                if real_count <= 0:
                    return None
                return (russian, fix, real_count)
            else:
                return (russian, fix, len(matches))
    return None

test_cases = [
    "Це самий великий кластер",                   # Expect: Russicism (1)
    "Це той самий кластер",                      # Expect: None
    "Це самий великий і той самий кластер",       # Expect: Russicism (1)
    "Це самий великий і та сама нода",           # Expect: Russicism (1) — BUT MIGHT BE BUGGED
    "Та сама нода і це самий великий кластер",    # Same as above, order changed
    "Та сама нода",                              # Expect: None
]

for t in test_cases:
    print(f"Input: {t}")
    print(f"Result: {check(t)}")
    print("-" * 40)
