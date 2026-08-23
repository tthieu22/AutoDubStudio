import re

class TranslationOutputSanitizer:
    """Translation Output Sanitizer.
    RESPONSIBILITY: Strictly FORMAT CORRECTION ONLY.
    - Strips markdown formatting (bold, italic, backticks, code blocks).
    - Removes surrounding quotes ('...', "...").
    - Removes common hallucinated prefixes ("Translation:", "Bản dịch:", "Dịch:").
    - Strips stray explanation suffixes.
    - Normalizes whitespace.

    CRITICAL RULE: DO NOT PERFORM ANY DICTIONARY / SEMANTIC REPLACEMENTS HERE.
    (e.g., Do NOT replace 爸爸 with Bố or Good night with Chúc ngủ ngon).
    """

    @staticmethod
    def sanitize(raw_text: str) -> str:
        if not raw_text:
            return ""

        text = raw_text.strip()

        # Remove markdown code block wrappers
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                text = "\n".join(lines[1:-1]).strip()

        # Strip bold/italic markdown formatting (*, **, _, __)
        text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
        text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)

        # Remove common prefix hallucinations ("Bản dịch:", "Translation:", "Dịch:", etc.)
        prefix_pattern = r'^(bản dịch|dịch|translation|vietnamese translation|việt nam):\s*'
        text = re.sub(prefix_pattern, '', text, flags=re.IGNORECASE).strip()

        # Strip matching surrounding quotes
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()

        # Remove trailing English commentary added by LLM (e.g. "This translation maintains...")
        text = re.split(r'\s+This translation\b', text, flags=re.IGNORECASE)[0].strip()
        text = re.split(r'\s+Note:\s+', text, flags=re.IGNORECASE)[0].strip()

        # Replace Chinese punctuation marks with standard Vietnamese equivalents
        text = text.replace("。", ".").replace("，", ",").replace("！", "!").replace("？", "?").replace("：", ":")

        # Remove non-Vietnamese foreign scripts if any lingering Chinese/CJK characters remain
        text = re.sub(r'[\u4e00-\u9fff]+', ' ', text)

        # Collapse whitespace
        return re.sub(r'\s+', ' ', text).strip()
