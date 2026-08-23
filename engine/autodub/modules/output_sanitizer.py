import re

class TranslationOutputSanitizer:
    """Translation Output Sanitizer.
    RESPONSIBILITY: Strictly FORMAT CORRECTION & FINAL ANSWER EXTRACTION.
    - Strips thinking blocks (<think>...</think>).
    - Removes conversational reasoning preambles ("Okay, let's...", "First, I need to...", "Let me analyze...").
    - Strips markdown formatting (bold, italic, backticks, code blocks).
    - Removes surrounding quotes ('...', "...").
    - Removes common hallucinated prefixes ("Translation:", "Bản dịch:", "Dịch:", "Vietnamese:").
    - Strips stray explanation suffixes / notes.
    - Normalizes punctuation and whitespace.

    CRITICAL RULE: DO NOT PERFORM ANY DICTIONARY / SEMANTIC REPLACEMENTS HERE.
    """

    @staticmethod
    def sanitize(raw_text: str) -> str:
        if not raw_text:
            return ""

        text = raw_text.strip()

        # 1. Strip <think>...</think> tags if present
        text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'^<think>[\s\S]*', '', text, flags=re.IGNORECASE).strip()

        # 2. Remove markdown code block wrappers
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                text = "\n".join(lines[1:-1]).strip()
        text = re.sub(r'^```(?:json|vietnamese|markdown)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)

        # 3. Strip bold/italic markdown formatting (*, **, _, __)
        text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
        text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)

        # 4. Remove preamble reasoning lines if any leaked into segment
        # e.g., "Okay, let's translate this sentence..." or "First, I need to understand..."
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_lines = []
        for line in lines:
            # Skip lines that are obvious English reasoning/instructions
            if re.match(r'^(okay|let me|first|here is|the chinese sentence|this sentence|in vietnamese|analyzing|understanding)\b', line, re.IGNORECASE):
                continue
            cleaned_lines.append(line)
        
        if cleaned_lines:
            text = " ".join(cleaned_lines).strip()
        elif lines:
            text = lines[-1].strip()

        # 5. Remove common prefix hallucinations ("Bản dịch:", "Translation:", "Dịch:", "Vietnamese:")
        prefix_pattern = r'^(bản dịch|dịch|translation|vietnamese translation|vietnamese|việt nam|final translation|kết quả dịch):\s*'
        text = re.sub(prefix_pattern, '', text, flags=re.IGNORECASE).strip()

        # 6. Strip matching surrounding quotes
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()

        # 7. Remove trailing English commentary / notes added by LLM
        text = re.split(r'\s+This translation\b', text, flags=re.IGNORECASE)[0].strip()
        text = re.split(r'\s+Note:\s+', text, flags=re.IGNORECASE)[0].strip()
        text = re.split(r'\s+Explanation:\s+', text, flags=re.IGNORECASE)[0].strip()

        # 8. Replace Chinese punctuation marks with standard Vietnamese equivalents
        text = text.replace("。", ".").replace("，", ",").replace("！", "!").replace("？", "?").replace("：", ":")

        # 9. Remove non-Vietnamese foreign scripts if any lingering Chinese/CJK characters remain
        text = re.sub(r'[\u4e00-\u9fff]+', ' ', text)

        # 10. Collapse whitespace
        return re.sub(r'\s+', ' ', text).strip()

