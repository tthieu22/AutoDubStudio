export interface DictionaryEntry {
  id: string;
  word: string;
  pronunciation: string;
  language: string;
  source: 'global' | 'project';
  enabled: boolean;
}

export interface DetectedUnknownEntity {
  word: string;
  suggestedPronunciation: string;
}

export interface DetectedEntityMismatch {
  segmentId: number;
  detectedWord: string;
  suggestedEntity: string;
}

export const COMMON_ENGLISH_STOPWORDS = new Set([
  'this', 'that', 'these', 'those', 'there', 'here',
  'i', 'you', 'he', 'she', 'it', 'we', 'they',
  'my', 'your', 'his', 'her', 'its', 'our', 'their',
  'the', 'a', 'an', 'and', 'but', 'or', 'so', 'if', 'because', 'as', 'until', 'while',
  'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
  'have', 'has', 'had', 'do', 'does', 'did',
  'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must',
  'hello', 'welcome', 'today', 'camping', 'okay', 'video', 'videos', 'please', 'thanks', 'thank', 'good', 'morning', 'afternoon'
]);

export const DEFAULT_GLOBAL_DICTIONARY: DictionaryEntry[] = [
  { id: 'g-1', word: 'Peppa Pig', pronunciation: 'Bép-pa Pích', language: 'en', source: 'global', enabled: true },
  { id: 'g-2', word: 'Peppa', pronunciation: 'Bép-pa', language: 'en', source: 'global', enabled: true },
  { id: 'g-3', word: 'George', pronunciation: 'Gi-oóc', language: 'en', source: 'global', enabled: true },
  { id: 'g-4', word: 'Suzy', pronunciation: 'Su-zi', language: 'en', source: 'global', enabled: true },
  { id: 'g-5', word: 'Mummy Pig', pronunciation: 'Mẹ Pig', language: 'en', source: 'global', enabled: true },
  { id: 'g-6', word: 'Daddy Pig', pronunciation: 'Bố Pig', language: 'en', source: 'global', enabled: true },
  { id: 'g-7', word: 'Rebecca', pronunciation: 'Rê-béc-ca', language: 'en', source: 'global', enabled: true },
  { id: 'g-8', word: 'Pedro', pronunciation: 'Pê-đrô', language: 'en', source: 'global', enabled: true },
  { id: 'g-9', word: 'Candy', pronunciation: 'Ken-đi', language: 'en', source: 'global', enabled: true },
  { id: 'g-10', word: 'Danny', pronunciation: 'Đen-ni', language: 'en', source: 'global', enabled: true },
  { id: 'g-11', word: 'Zoe', pronunciation: 'Zô-i', language: 'en', source: 'global', enabled: true },
  { id: 'g-12', word: 'Emily', pronunciation: 'E-mi-li', language: 'en', source: 'global', enabled: true },
  { id: 'g-13', word: 'Richard', pronunciation: 'Ri-chạt', language: 'en', source: 'global', enabled: true },
  { id: 'g-14', word: 'Edmond', pronunciation: 'Ét-mơn', language: 'en', source: 'global', enabled: true },
  { id: 'g-15', word: 'podcast', pronunciation: 'pót cát', language: 'en', source: 'global', enabled: true },
  { id: 'g-16', word: 'video', pronunciation: 'vi-đê-ô', language: 'en', source: 'global', enabled: true },
  { id: 'g-17', word: 'videos', pronunciation: 'vi-đê-ô', language: 'en', source: 'global', enabled: true },
  { id: 'g-18', word: 'online', pronunciation: 'on-lai', language: 'en', source: 'global', enabled: true },
  { id: 'g-19', word: 'website', pronunciation: 'trang web', language: 'en', source: 'global', enabled: true },
  { id: 'g-20', word: 'audio', pronunciation: 'ô-đi-ô', language: 'en', source: 'global', enabled: true },
  { id: 'g-21', word: 'facebook', pronunciation: 'phây-sbút', language: 'en', source: 'global', enabled: true },
  { id: 'g-22', word: 'youtube', pronunciation: 'du-túp', language: 'en', source: 'global', enabled: true },
  { id: 'g-23', word: 'google', pronunciation: 'gút-gồ', language: 'en', source: 'global', enabled: true },
  { id: 'g-24', word: 'app', pronunciation: 'áp', language: 'en', source: 'global', enabled: true },
  { id: 'g-25', word: 'clip', pronunciation: 'clíp', language: 'en', source: 'global', enabled: true },
  { id: 'g-26', word: 'Daddy', pronunciation: 'Bố', language: 'en', source: 'global', enabled: true },
  { id: 'g-27', word: 'Mummy', pronunciation: 'Mẹ', language: 'en', source: 'global', enabled: true },
  { id: 'g-28', word: 'OK', pronunciation: 'ô kê', language: 'en', source: 'global', enabled: true },
  { id: 'g-29', word: 'Okay', pronunciation: 'ô kê', language: 'en', source: 'global', enabled: true },
  { id: 'g-30', word: 'Bye-bye', pronunciation: 'bái bai', language: 'en', source: 'global', enabled: true },
  { id: 'g-31', word: 'Bye', pronunciation: 'bái bai', language: 'en', source: 'global', enabled: true },
  { id: 'g-32', word: 'Hello', pronunciation: 'hê-lô', language: 'en', source: 'global', enabled: true },
  { id: 'g-33', word: 'Hi', pronunciation: 'hai', language: 'en', source: 'global', enabled: true },
  { id: 'g-34', word: 'Yes', pronunciation: 'dét', language: 'en', source: 'global', enabled: true },
  { id: 'g-35', word: 'No', pronunciation: 'nô', language: 'en', source: 'global', enabled: true },
  { id: 'g-36', word: 'Boss', pronunciation: 'sếp', language: 'en', source: 'global', enabled: true },
  { id: 'g-37', word: 'VIP', pronunciation: 'víp', language: 'en', source: 'global', enabled: true },
  { id: 'g-38', word: 'Game', pronunciation: 'gêm', language: 'en', source: 'global', enabled: true },
  { id: 'g-39', word: 'Show', pronunciation: 'sô', language: 'en', source: 'global', enabled: true },
  { id: 'g-40', word: 'Team', pronunciation: 'tim', language: 'en', source: 'global', enabled: true },
  { id: 'g-41', word: 'Fan', pronunciation: 'phan', language: 'en', source: 'global', enabled: true },
  { id: 'g-42', word: 'Link', pronunciation: 'linh', language: 'en', source: 'global', enabled: true },
  { id: 'g-43', word: 'Pass', pronunciation: 'pát', language: 'en', source: 'global', enabled: true },
  { id: 'g-44', word: 'Deal', pronunciation: 'điêu', language: 'en', source: 'global', enabled: true },
  { id: 'g-45', word: 'Ship', pronunciation: 'síp', language: 'en', source: 'global', enabled: true },
  { id: 'g-46', word: 'TikTok', pronunciation: 'Tích-tốc', language: 'en', source: 'global', enabled: true },
  { id: 'g-47', word: 'iPhone', pronunciation: 'Ai-phôn', language: 'en', source: 'global', enabled: true },
  { id: 'g-48', word: 'KFC', pronunciation: 'Cây-ép-xi', language: 'en', source: 'global', enabled: true },
  { id: 'g-49', word: 'Live', pronunciation: 'lai', language: 'en', source: 'global', enabled: true },
  { id: 'g-50', word: 'Stream', pronunciation: 'sờ-trim', language: 'en', source: 'global', enabled: true },
  { id: 'g-51', word: 'Vlog', pronunciation: 'vơ-lóc', language: 'en', source: 'global', enabled: true }
];

export class PronunciationDictionaryService {
  private static STORAGE_KEY_PREFIX = 'autodub_dict_';
  private static OLLAMA_ENDPOINT = 'http://localhost:11434/api/generate';
  private static DEFAULT_MODEL = 'qwen2.5:3b';

  /**
   * Scan entire subtitle list for foreign / English / acronym words not yet registered in active dictionary.
   */
  public static extractForeignWords(subtitles: any[], existingDict: DictionaryEntry[]): string[] {
    const existingWords = new Set(
      existingDict
        .filter(e => e.enabled && e.word.trim())
        .map(e => e.word.trim().toLowerCase())
    );

    const foundWordsMap = new Map<string, number>();

    subtitles.forEach(seg => {
      const text = `${seg.translated_text || ''} ${seg.text || ''} ${seg.original_text || ''}`;
      // Regex match words with Latin characters (2+ letters, including hyphens)
      const matches = text.match(/\b[A-Za-z][A-Za-z0-9\-_]{1,}\b/g) || [];
      matches.forEach(w => {
        const clean = w.trim();
        const lower = clean.toLowerCase();
        if (
          clean.length >= 2 &&
          !existingWords.has(lower) &&
          !COMMON_ENGLISH_STOPWORDS.has(lower) &&
          !/^\d+$/.test(clean)
        ) {
          foundWordsMap.set(clean, (foundWordsMap.get(clean) || 0) + 1);
        }
      });
    });

    // Return unique words sorted by frequency descending
    return Array.from(foundWordsMap.keys()).slice(0, 30);
  }

  /**
   * Request Qwen 2.5:3B to generate natural Vietnamese TTS pronunciations for words.
   */
  public static async generatePhoneticsWithAi(words: string[]): Promise<Record<string, string>> {
    if (!words || words.length === 0) return {};

    const wordListStr = words.map(w => `"${w}"`).join(', ');
    const prompt = `Bạn là chuyên gia ngữ âm và lồng tiếng phim Tiếng Việt (TTS Audio Dubbing).
Nhiệm vụ: Chuyển danh sách các từ tiếng Anh / tên riêng / từ viết tắt sau thành phiên âm Tiếng Việt chuẩn để máy đọc TTS (Piper TTS) phát âm tự nhiên, dễ nghe và đúng ngữ điệu người Việt.

Danh sách từ cần phiên âm: [${wordListStr}]

QUY TẮC PHIÊN ÂM:
1. Phiên âm tự nhiên theo cách người Việt Nam hay đọc (Ví dụ: Peppa -> Pép-pa, George -> Gióoc, iPhone -> Ai-phôn, OK -> ô kê, TikTok -> Tích-tốc, KFC -> Cây-ép-xi, Superman -> Siêu nhân).
2. Dùng dấu gạch nối giữa các âm tiết phiên âm nếu là từ ghép (ví dụ: Ai-phôn, Pép-pa).
3. Chỉ trả về duy nhất 1 JSON object hợp lệ mapping: {"Từ_Gốc": "Phiên_Âm_Tiếng_Việt"}. Không viết giải thích thêm.

JSON:`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 20000);

      const response = await fetch(this.OLLAMA_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          model: this.DEFAULT_MODEL,
          prompt: prompt,
          stream: false,
          options: {
            temperature: 0.2,
            top_p: 0.9,
            num_predict: 500
          }
        })
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        const rawResponse = data.response || '';
        
        // Extract JSON object from LLM response
        const jsonMatch = rawResponse.match(/\{[\s\S]*?\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          const result: Record<string, string> = {};
          for (const [k, v] of Object.entries(parsed)) {
            if (typeof v === 'string' && v.trim()) {
              result[k.trim()] = (v as string).trim();
            }
          }
          if (Object.keys(result).length > 0) {
            return result;
          }
        }
      }
    } catch (e) {
      console.warn('Ollama Qwen2.5 phonetic generation failed, falling back to rule engine:', e);
    }

    // Deterministic Rule Fallback if Ollama is not running
    const fallbackMap: Record<string, string> = {};
    words.forEach(w => {
      const lower = w.toLowerCase();
      if (lower === 'ok' || lower === 'okay') fallbackMap[w] = 'ô kê';
      else if (lower === 'peppa') fallbackMap[w] = 'Pép-pa';
      else if (lower === 'george') fallbackMap[w] = 'Gióoc';
      else if (lower === 'iphone') fallbackMap[w] = 'Ai-phôn';
      else if (lower === 'tiktok') fallbackMap[w] = 'Tích-tốc';
      else if (lower === 'kfc') fallbackMap[w] = 'Cây-ép-xi';
      else if (lower === 'bye' || lower === 'byebye') fallbackMap[w] = 'bái bai';
      else if (lower === 'hello' || lower === 'hi') fallbackMap[w] = 'hê-lô';
      else fallbackMap[w] = w;
    });

    return fallbackMap;
  }

  public static getDictionaryForProject(projectDir: string): DictionaryEntry[] {
    const key = this.STORAGE_KEY_PREFIX + projectDir;
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.error('Failed to load dictionary from localStorage', e);
    }
    return [...DEFAULT_GLOBAL_DICTIONARY];
  }

  public static saveDictionaryForProject(projectDir: string, entries: DictionaryEntry[]): void {
    const key = this.STORAGE_KEY_PREFIX + projectDir;
    try {
      localStorage.setItem(key, JSON.stringify(entries));
    } catch (e) {
      console.error('Failed to save dictionary to localStorage', e);
    }
  }

  /**
   * TẦNG 3 — TTS Normalizer (Deterministic Rule Engine):
   * Rule engine for numbers, time formats, percentages, currency, symbols, and repeated character expressions.
   */
  public static applyLayer3RuleEngine(input: string): string {
    if (!input) return '';
    let text = input;

    // 1. Time formats (e.g. 10:30 -> 10 giờ 30, 08:15 -> 8 giờ 15)
    text = text.replace(/\b(\d{1,2}):(\d{2})\b/g, (_m, h, min) => `${parseInt(h, 10)} giờ ${parseInt(min, 10)}`);

    // 2. Percentages (e.g. 20% -> 20 phần trăm)
    text = text.replace(/(\d+)%/g, '$1 phần trăm');

    // 3. Currency (e.g. $100 -> 100 đô-la, 100$ -> 100 đô-la)
    text = text.replace(/\$(\d+)/g, '$1 đô-la');
    text = text.replace(/(\d+)\$/g, '$1 đô-la');

    const capitalizeMatch = (replacement: string, matchText: string) => {
      if (matchText && matchText[0] === matchText[0].toUpperCase()) {
        return replacement.charAt(0).toUpperCase() + replacement.slice(1);
      }
      return replacement;
    };

    // 4. Repeated character emotional prolongations (Hiiii -> Hi hi, Wowww -> Oa, Nooo -> Khônggg)
    text = text.replace(/\b(h[iìíỉĩị]{2,})\b/gi, (m) => capitalizeMatch('hi hi', m));
    text = text.replace(/\b(w[oòóỏõọ]{2,}w*|w[oòóỏõọ]+w{2,})\b/gi, (m) => capitalizeMatch('oa', m));
    text = text.replace(/\b(h[eèéẻẽẹ]ll[oòóỏõọ]{2,})\b/gi, (m) => capitalizeMatch('he-lô', m));
    text = text.replace(/\b(n[oòóỏõọ]{3,})\b/gi, (m) => capitalizeMatch('khônggg', m));
    text = text.replace(/\b(g[oòóỏõọ]{2,})\b/gi, (m) => capitalizeMatch('đi đi', m));
    text = text.replace(/\b(y[eèéẻẽẹ]*s{2,})\b/gi, (m) => capitalizeMatch('vânggg', m));

    // 5. Symbols spoken replacements
    text = text.replace(/%/g, ' phần trăm');
    text = text.replace(/\$/g, ' đô-la');
    text = text.replace(/&/g, ' và ');
    text = text.replace(/@/g, ' a-còng ');

    return text.replace(/\s+/g, ' ').trim();
  }

  /**
   * Protected Entity Replacement Mechanism (Longest Match First + Token Protection):
   * 1. Sort dictionary entries by length descending (Longest Match First).
   * 2. Replace matched entity occurrences with protected tokens (e.g. __ENTITY_TOKEN_0__).
   * 3. Run Rule Engine on remaining text.
   * 4. Restore protected tokens with their target pronunciations.
   */
  public static processTextWithEntityProtection(input: string, dictionary: DictionaryEntry[]): string {
    if (!input || !input.trim()) return '';

    let workingText = input;
    const tokenMap: Map<string, string> = new Map();

    // 1. Sort dictionary by word length descending (Longest Match First)
    const activeEntries = dictionary
      .filter(e => e.enabled && e.word.trim().length > 0)
      .sort((a, b) => b.word.length - a.word.length);

    // 2. Tokenize entities
    activeEntries.forEach((entry, idx) => {
      const escaped = entry.word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`\\b${escaped}\\b`, 'gi');

      if (regex.test(workingText)) {
        const token = `__ENTITY_TOKEN_${idx}__`;
        tokenMap.set(token, entry.pronunciation);
        workingText = workingText.replace(regex, token);
      }
    });

    // 3. Apply Layer 3 Rule Normalization on text containing tokens
    let normalized = this.applyLayer3RuleEngine(workingText);

    // 4. Restore protected entity tokens to their phonetic pronunciations
    tokenMap.forEach((pronunciation, token) => {
      const tokenRegex = new RegExp(token, 'g');
      normalized = normalized.replace(tokenRegex, pronunciation);
    });

    return normalized.replace(/\s+/g, ' ').trim();
  }

  /**
   * Detect unmapped Proper Nouns / Foreign Entities in text with Stopwords filtering.
   */
  public static detectUnknownEntities(input: string, dictionary: DictionaryEntry[]): DetectedUnknownEntity[] {
    if (!input) return [];

    const activeWords = new Set(dictionary.filter(e => e.enabled).map(e => e.word.toLowerCase()));
    const detected: DetectedUnknownEntity[] = [];

    // Match English titles & Proper Nouns (e.g. Mr. Alexander Thompson, Dr. Smith)
    const namePattern = /\b(Mr\.|Mrs\.|Dr\.|Prof\.)?\s*([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)\b/g;
    let match;

    while ((match = namePattern.exec(input)) !== null) {
      const fullEntity = match[0].trim();
      const entityLower = fullEntity.toLowerCase();

      // Filter out common English stopwords and existing dictionary terms
      if (!activeWords.has(entityLower) && !COMMON_ENGLISH_STOPWORDS.has(entityLower)) {
        // Generate automatic phonetic suggestion
        const suggested = fullEntity
          .replace(/Mr\./gi, 'Mít-tơ')
          .replace(/Dr\./gi, 'Đốc-tơ')
          .replace(/Mrs\./gi, 'Mít-xít')
          .replace(/Prof\./gi, 'Giáo sư');

        if (!detected.some(d => d.word.toLowerCase() === entityLower)) {
          detected.push({ word: fullEntity, suggestedPronunciation: suggested });
        }
      }
    }

    return detected;
  }

  /**
   * Detect Entity Mismatch (e.g. "Pepper" transcribed by STT instead of "Peppa").
   */
  public static detectEntityMismatches(segments: any[]): DetectedEntityMismatch[] {
    const mismatches: DetectedEntityMismatch[] = [];
    const commonPhoneticMismatches = [
      { wrong: /\bPepper\b/gi, correct: 'Peppa' },
      { wrong: /\bJorg\b/gi, correct: 'George' },
      { wrong: /\bSuzi\b/gi, correct: 'Suzy' }
    ];

    segments.forEach(seg => {
      const text = `${seg.text || ''} ${seg.translated_text || ''}`;
      for (const m of commonPhoneticMismatches) {
        if (m.wrong.test(text)) {
          mismatches.push({
            segmentId: seg.id,
            detectedWord: 'Pepper',
            suggestedEntity: m.correct
          });
        }
      }
    });

    return mismatches;
  }

  public static processText(input: string, dictionary: DictionaryEntry[]): string {
    return this.processTextWithEntityProtection(input, dictionary);
  }
}
