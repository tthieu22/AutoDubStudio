import urllib.request
import json
import time
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def translate_google_free(text, target_lang="vi"):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            translated_text = "".join([sentence[0] for sentence in result[0] if sentence[0]])
            return translated_text
    except Exception as e:
        print("Error during translation:", e)
        return text

if __name__ == "__main__":
    sample_text = "Welcome to AutoDubStudio. Today we will explore local AI video translation and dubbing technology."
    print("Original Text:", sample_text)
    
    start_time = time.time()
    translated = translate_google_free(sample_text)
    elapsed = time.time() - start_time
    
    print("Translated Text:", translated)
    print(f"Translation completed in {elapsed:.4f} seconds.")

