import sys
from pathlib import Path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))
from autodub.modules.ollama_client import OllamaClient

c = OllamaClient()
prompt = """Task: Translate Chinese subtitle to natural Vietnamese dialogue.
LOCKED ENTITY MEMORY:
- 爸爸 = Bố
- 妈妈 = Mẹ

CHINESE TEXT: "爸爸和妈妈去买菜。"

Output JSON format: {"translation": "Bản dịch Tiếng Việt"}"""

res = c.generate(prompt=prompt, model="qwen3:4b", temperature=0.15, format_json=False)
print("Qwen3:4b Raw Output:\n", res)
