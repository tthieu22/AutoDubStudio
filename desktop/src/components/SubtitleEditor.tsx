import React, { useState, useEffect, useRef } from 'react';
import { 
  Save, RotateCcw, Sparkles, AlertCircle, Search, 
  Globe, Volume2, Edit3, BookOpen, Undo, Redo, CheckCircle2, 
  AlertTriangle, Clock, Zap, Check, Play, User, Sliders, ShieldCheck, ArrowRight
} from 'lucide-react';
import { PythonEngineService } from '../services/pythonEngine';
import { editorStore } from '../editor/state/editorStore';
import { PronunciationDictionaryService, DictionaryEntry } from '../services/pronunciationDictionary';
import { TtsValidatorService, PreTtsValidationResult } from '../services/ttsValidator';
import { TranslationQaService } from '../services/translationQa';
import { TranslationRepairService } from '../services/translationRepair';
import { TtsAdaptationEngine } from '../services/ttsAdaptation';
import { PronunciationDictionaryModal } from './PronunciationDictionaryModal';
import { BulkVietsubModal } from './BulkVietsubModal';
import { PreTtsValidationModal } from './PreTtsValidationModal';

interface SubtitleEditorProps {
  projectDir: string;
  activeTab?: string;
  onProceedToVoices: () => void;
}

export const SubtitleEditor: React.FC<SubtitleEditorProps> = ({ projectDir, activeTab, onProceedToVoices }) => {
  const [subtitles, setSubtitles] = useState<any[]>([]);
  const [selectedSegId, setSelectedSegId] = useState<number | null>(null);
  const [selectedSegIds, setSelectedSegIds] = useState<number[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [dictionary, setDictionary] = useState<DictionaryEntry[]>([]);

  // Modals state
  const [isDictModalOpen, setIsDictModalOpen] = useState(false);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  const [isPreTtsModalOpen, setIsPreTtsModalOpen] = useState(false);
  const [validationResult, setValidationResult] = useState<PreTtsValidationResult | null>(null);

  // Preview Audio state
  const [previewingSegId, setPreviewingSegId] = useState<number | null>(null);
  const [previewMessage, setPreviewMessage] = useState<string | null>(null);

  // Undo / Redo History Stack
  const historyStackRef = useRef<any[][]>([]);
  const historyIndexRef = useRef<number>(-1);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);

  useEffect(() => {
    if (activeTab === 'subtitles' || !activeTab) {
      loadSubtitles();
      const loadedDict = PronunciationDictionaryService.getDictionaryForProject(projectDir);
      setDictionary(loadedDict);
    }
  }, [projectDir, activeTab]);

  const pushHistoryState = (newSubtitles: any[]) => {
    const clone = JSON.parse(JSON.stringify(newSubtitles));
    // Truncate redo states if pushing new state
    const currentStack = historyStackRef.current.slice(0, historyIndexRef.current + 1);
    currentStack.push(clone);
    historyStackRef.current = currentStack;
    historyIndexRef.current = currentStack.length - 1;
    setCanUndo(historyIndexRef.current > 0);
    setCanRedo(false);
  };

  const handleUndo = () => {
    if (historyIndexRef.current > 0) {
      historyIndexRef.current--;
      const restored = JSON.parse(JSON.stringify(historyStackRef.current[historyIndexRef.current]));
      setSubtitles(restored);
      setHasChanges(true);
      setCanUndo(historyIndexRef.current > 0);
      setCanRedo(historyIndexRef.current < historyStackRef.current.length - 1);
    }
  };

  const handleRedo = () => {
    if (historyIndexRef.current < historyStackRef.current.length - 1) {
      historyIndexRef.current++;
      const restored = JSON.parse(JSON.stringify(historyStackRef.current[historyIndexRef.current]));
      setSubtitles(restored);
      setHasChanges(true);
      setCanUndo(historyIndexRef.current > 0);
      setCanRedo(historyIndexRef.current < historyStackRef.current.length - 1);
    }
  };

  const [projectStyle, setProjectStyle] = useState<string>('general');

  const loadSubtitles = async () => {
    try {
      try {
        const projJson = await PythonEngineService.readProjectJson(projectDir);
        if (projJson && projJson.settings) {
          setProjectStyle(projJson.settings.translation_style || 'general');
        }
      } catch (pErr) {
        console.error('Failed to read project style:', pErr);
      }

      const data = await PythonEngineService.readSubtitles(projectDir);
      const normalized = (data || []).map((seg: any, idx: number) => {
        const id = seg.id || idx + 1;
        const start = Number(seg.start || seg.startTime || 0);
        const end = Number(seg.end || seg.endTime || start + 2.0);
        const translated = seg.translated_text || seg.translation || '';
        const ttsText = seg.tts_text || (translated ? PronunciationDictionaryService.processText(translated, dictionary) : '');
        const speed = Number(seg.speed || seg.speedFactor || 1.0);

        return {
          ...seg,
          id,
          start,
          end,
          text: seg.text || seg.original_text || '',
          translated_text: translated,
          tts_text: ttsText,
          tts_text_override: seg.tts_text_override || false,
          speaker: seg.speaker || 'Speaker 1',
          speed: speed,
          tts: seg.tts || { status: translated ? 'READY' : 'NOT_GENERATED' },
          dirty: seg.dirty || { translation: false, timing: false, tts: false }
        };
      });

      setSubtitles(normalized);
      if (normalized.length > 0) setSelectedSegId(normalized[0].id);
      setHasChanges(false);

      // Initialize history stack
      historyStackRef.current = [JSON.parse(JSON.stringify(normalized))];
      historyIndexRef.current = 0;
      setCanUndo(false);
      setCanRedo(false);
    } catch (err) {
      console.error('Failed to load subtitles:', err);
    }
  };

  const handleFieldChange = (id: number, field: string, value: any) => {
    const updated = subtitles.map(s => {
      if (s.id === id) {
        const newSeg = { ...s, [field]: value };

        if (!newSeg.dirty) newSeg.dirty = {};
        if (!newSeg.tts) newSeg.tts = {};

        if (field === 'translated_text') {
          newSeg.dirty.translation = true;
          // Synchronize tts_text unless manual override
          if (!newSeg.tts_text_override) {
            newSeg.tts_text = PronunciationDictionaryService.processText(value, dictionary);
          }
          newSeg.tts.status = 'NEEDS_REGENERATION';
          newSeg.tts.audioPath = null;
        } else if (field === 'tts_text') {
          newSeg.tts_text_override = true;
          newSeg.dirty.tts = true;
          newSeg.tts.status = 'NEEDS_REGENERATION';
          newSeg.tts.audioPath = null;
        } else if (field === 'start' || field === 'end') {
          newSeg.dirty.timing = true;
        } else if (field === 'speed') {
          newSeg.dirty.tts = true;
          newSeg.tts.status = 'NEEDS_REGENERATION';
        }

        return newSeg;
      }
      return s;
    });

    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);

    // Sync timeline clip if applicable
    const clipId = `clip-sub-${id}`;
    const targetClip = editorStore.getComposition().clips.find(c => c.id === clipId);
    if (targetClip) {
      if (field === 'translated_text' || field === 'text') {
        editorStore.updateClip(clipId, {
          name: `Sub #${id}: ${(value || '').substring(0, 16)}...`,
          subtitleProps: { ...targetClip.subtitleProps, text: value }
        });
      } else if (field === 'start') {
        editorStore.updateClip(clipId, { startTime: Number(value) });
      } else if (field === 'end') {
        editorStore.updateClip(clipId, { duration: Math.max(0.2, Number(value) - targetClip.startTime) });
      }
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await PythonEngineService.writeSubtitles(projectDir, subtitles);
      setHasChanges(false);
    } catch (err) {
      alert(`Lưu phụ đề thất bại: ${err}`);
    } finally {
      setIsSaving(false);
    }
  };

  const translateEnglishToVietnameseAi = async (origText: string, prevContext: string = '', nextContext: string = ''): Promise<string> => {
    if (!origText || !origText.trim()) return '';

    const cleanText = origText.trim();
    const prompt = `You are a professional English-to-Vietnamese subtitle translator for cartoon and video dubbing.
Your task is to translate the following English subtitle text into natural, spoken Vietnamese dialogue.

ENGLISH SUBTITLE:
"${cleanText}"

SURROUNDING DIALOG CONTEXT:
Previous line: "${prevContext || 'N/A'}"
Next line: "${nextContext || 'N/A'}"

TRANSLATION RULES:
1. Translate meaning and intent of the entire sentence, NOT individual words literally.
2. Recognize common English expressions, idioms, greetings, phrasal verbs, and conversational phrases.
3. Never translate fixed expressions or greetings literally when that produces unnatural Vietnamese.
4. Use natural Vietnamese suitable for spoken dialogue in cartoons/movies.
5. Preserve character names consistently (e.g. Daddy Pig -> Bố Pig / Ba Heo, Mummy Pig -> Mẹ Pig / Mẹ Heo).
6. Do not add information that does not exist in the original.
7. The output must sound like natural Vietnamese dialogue.

EXAMPLES:
- "Good night, Daddy Pig." -> "Chúc ngủ ngon, Bố Pig." (NOT "Đêm nay, Ba Heo.")
- "How are you?" -> "Bạn khỏe không?" (NOT "Bạn là thế nào?")
- "Come on!" -> "Nào!" / "Thôi nào!" (NOT "Đến đi!")
- "What's up?" -> "Có chuyện gì vậy?"

VIETNAMESE TRANSLATION:`;

    try {
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'qwen2.5:3b',
          prompt,
          stream: false
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data && data.response) {
          const res = data.response.trim().replace(/^["']|["']$/g, '');
          if (res) return res;
        }
      }
    } catch (e) {
      console.warn('[AI TRANSLATION] Ollama LLM server unreachable at http://localhost:11434/api/generate', e);
    }

    return cleanText;
  };

  // Feature 3: VIETSUB TOÀN BỘ (100% Dynamic Ollama AI Translation)
  const handleFullVietsub = async () => {
    setIsTranslating(true);
    try {
      const updated = [...subtitles];
      for (let i = 0; i < updated.length; i++) {
        const s = updated[i];
        const origText = s.text || s.original_text || '';
        const prevContext = i > 0 ? (updated[i - 1].translated_text || updated[i - 1].text || '') : '';
        const nextContext = i < updated.length - 1 ? (updated[i + 1].translated_text || updated[i + 1].text || '') : '';

        const trans = await translateEnglishToVietnameseAi(origText, prevContext, nextContext);
        const ttsText = s.tts_text_override ? s.tts_text : PronunciationDictionaryService.processText(trans, dictionary);

        console.log(`[VIETSUB DYNAMIC AI] segment=#${s.id} original="${origText}" translated="${trans}"`);

        updated[i] = {
          ...s,
          text: origText,
          original_text: origText,
          translated_text: trans,
          tts_text: ttsText,
          tts: { ...s.tts, status: 'NEEDS_REGENERATION' },
          dirty: { ...s.dirty, translation: true, tts: true }
        };
      }

      setSubtitles(updated);
      setHasChanges(true);
      pushHistoryState(updated);

      await PythonEngineService.writeSubtitles(projectDir, updated);
      console.log('[VIETSUB] Successfully persisted translatedText into translation.json');
    } catch (err) {
      console.error('Failed to run VIETSUB TOÀN BỘ:', err);
    } finally {
      setIsTranslating(false);
    }
  };

  // Feature 17: VIỆT HÓA TTS TOÀN BỘ
  const handleFullTtsNormalization = async () => {
    let autoGenCount = 0;
    let manualPreservedCount = 0;

    const updated = subtitles.map(s => {
      const currentTrans = s.translated_text || s.text || '';
      if (s.tts_text_override) {
        manualPreservedCount++;
        return s;
      }

      const normalizedTts = PronunciationDictionaryService.processText(currentTrans, dictionary);
      autoGenCount++;

      console.log(`[TTS PREPARATION] segment=#${s.id} translated="${currentTrans}" tts="${normalizedTts}"`);

      return {
        ...s,
        tts_text: normalizedTts,
        tts: { ...s.tts, status: 'NEEDS_REGENERATION' },
        dirty: { ...s.dirty, tts: true }
      };
    });

    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);

    await PythonEngineService.writeSubtitles(projectDir, updated);
    console.log('[TTS PREPARATION] Successfully persisted ttsText into translation.json');
    alert(`✓ Đã Việt hóa TTS xong cho ${subtitles.length} segments!\n- Tự động tạo: ${autoGenCount} câu\n- Giữ nguyên tùy chỉnh tay: ${manualPreservedCount} câu`);
  };

  // Single Segment Auto Generate TTS Text with Semantic Drift Protection
  const handleSingleAutoGenerateTtsText = async (segId: number) => {
    const seg = subtitles.find(s => s.id === segId);
    if (!seg) return;

    const sourceVietsub = (seg.translated_text || seg.text || '').trim();
    let candidateTts = PronunciationDictionaryService.processText(sourceVietsub, dictionary);

    // Semantic Drift Protection: If candidate generates gibberish, fallback to clean source Vietsub
    if (/Byé|Dàp-dàp/i.test(candidateTts) && !/Byé|Dàp-dàp/i.test(sourceVietsub)) {
      candidateTts = sourceVietsub;
    }

    const updated = subtitles.map(s => {
      if (s.id === segId) {
        return {
          ...s,
          tts_text: candidateTts,
          tts_text_override: false,
          tts: { ...s.tts, status: 'NEEDS_REGENERATION' },
          dirty: { ...s.dirty, tts: true }
        };
      }
      return s;
    });

    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);
    await PythonEngineService.writeSubtitles(projectDir, updated);

    console.log(`[TTS REGENERATE] segment=#${segId} source="${sourceVietsub}" tts="${candidateTts}"`);
  };

  // AI Translation Repair Handlers
  const [aiSuggestionMap, setAiSuggestionMap] = useState<Record<number, any>>({});

  const handleSingleAiRepairTranslation = async (segId: number) => {
    const seg = subtitles.find(s => s.id === segId);
    if (!seg) return;

    const qaRes = TranslationQaService.checkSegmentQa(seg);
    const repairRes = await TranslationRepairService.repairSegmentAi(seg, qaRes.issues);

    setAiSuggestionMap(prev => ({ ...prev, [segId]: repairRes }));

    // If confidence >= 0.90, auto apply repaired Vietsub & update tts_text
    if (repairRes.confidence >= 0.90) {
      const candidateTts = PronunciationDictionaryService.processText(repairRes.suggestedTranslation, dictionary);
      const updated = subtitles.map(s => {
        if (s.id === segId) {
          return {
            ...s,
            translated_text: repairRes.suggestedTranslation,
            tts_text: candidateTts,
            tts_text_override: false,
            dirty: { ...s.dirty, translation: true, tts: true },
            tts: { ...s.tts, status: 'NEEDS_REGENERATION' }
          };
        }
        return s;
      });

      setSubtitles(updated);
      setHasChanges(true);
      pushHistoryState(updated);
      await PythonEngineService.writeSubtitles(projectDir, updated);
    }
  };

  const handleApplyAiSuggestion = async (segId: number) => {
    const suggestion = aiSuggestionMap[segId];
    if (!suggestion) return;

    const candidateTts = PronunciationDictionaryService.processText(suggestion.suggestedTranslation, dictionary);
    const updated = subtitles.map(s => {
      if (s.id === segId) {
        return {
          ...s,
          translated_text: suggestion.suggestedTranslation,
          tts_text: candidateTts,
          tts_text_override: false,
          dirty: { ...s.dirty, translation: true, tts: true },
          tts: { ...s.tts, status: 'NEEDS_REGENERATION' }
        };
      }
      return s;
    });

    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);

    setAiSuggestionMap(prev => {
      const copy = { ...prev };
      delete copy[segId];
      return copy;
    });

    await PythonEngineService.writeSubtitles(projectDir, updated);
  };

  const handleAiRepairAll = async () => {
    const projectQa = TranslationQaService.checkProjectQa(subtitles);
    if (projectQa.flaggedCount === 0) {
      alert('✓ Toàn bộ bản dịch đã đạt tiêu chuẩn QA! Không có lỗi cần sửa.');
      return;
    }

    const { repairedSegments, repairedCount, autoAcceptedCount } = await TranslationRepairService.repairAllSegmentsAi(subtitles, projectQa.results);

    setSubtitles(repairedSegments);
    setHasChanges(true);
    pushHistoryState(repairedSegments);

    await PythonEngineService.writeSubtitles(projectDir, repairedSegments);

    alert(`✓ AI đã tự động sửa thành công cho ${repairedCount} câu thoại!\n- Tự động áp dụng (Confidence >= 90%): ${autoAcceptedCount} câu`);
  };

  // Feature 9: FIT TTS TO SEGMENT (Natural Duration Fitting)
  const handleFitTtsToSegment = async (segId: number) => {
    const seg = subtitles.find(s => s.id === segId);
    if (!seg) return;

    const timing = TtsValidatorService.validateSegmentTiming(seg);
    const currentTts = (seg.tts_text || seg.translated_text || '').trim();

    // 1. Try AI Text Optimization
    const result = await TtsAdaptationEngine.optimizeTtsTextForDuration(currentTts, timing.segmentDuration);
    let updatedSeg = { ...seg };

    if (result.fits || result.canFitNaturally) {
      updatedSeg.tts_text = result.optimizedTtsText;
      updatedSeg.dirty = { ...seg.dirty, tts: true };
      updatedSeg.tts = { ...seg.tts, status: 'NEEDS_REGENERATION' };
    } else {
      // 2. Extend segment end time if text optimization isn't enough
      const newEnd = Number((seg.start + timing.effectiveTtsDuration + 0.1).toFixed(2));
      updatedSeg.end = newEnd;
      updatedSeg.dirty = { ...seg.dirty, timing: true };
    }

    const updated = subtitles.map(s => s.id === segId ? updatedSeg : s);
    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);

    // Sync clip in editorStore
    const clipId = `clip-sub-${segId}`;
    const targetClip = editorStore.getComposition().clips.find(c => c.id === clipId);
    if (targetClip) {
      editorStore.updateClip(clipId, { duration: Math.max(0.2, updatedSeg.end - targetClip.startTime) });
    }

    await PythonEngineService.writeSubtitles(projectDir, updated);
    console.log(`[FIT TTS] segment=#${segId} updated end=${updatedSeg.end} tts="${updatedSeg.tts_text}"`);
  };

  // Bulk actions on selected rows
  const handleSelectAllRows = () => {
    if (selectedSegIds.length === subtitles.length) {
      setSelectedSegIds([]);
    } else {
      setSelectedSegIds(subtitles.map(s => s.id));
    }
  };

  const handleToggleRowSelect = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (selectedSegIds.includes(id)) {
      setSelectedSegIds(selectedSegIds.filter(i => i !== id));
    } else {
      setSelectedSegIds([...selectedSegIds, id]);
    }
  };

  const handleFitSelectedSegments = () => {
    if (selectedSegIds.length === 0) return;
    const updated = subtitles.map(seg => {
      if (selectedSegIds.includes(seg.id)) {
        const val = TtsValidatorService.validateSegmentTiming(seg);
        const recSpeed = TtsValidatorService.recommendSpeedFactor(val.estimatedTtsDuration, val.segmentDuration);
        return {
          ...seg,
          speed: recSpeed,
          tts: { ...seg.tts, status: 'NEEDS_REGENERATION' },
          dirty: { ...seg.dirty, tts: true }
        };
      }
      return seg;
    });

    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);
  };

  // Feature 12 & 16: Pre-TTS Validation & Proceed
  const handleProceedClick = () => {
    const result = TtsValidatorService.validatePreTtsChecklist(subtitles);
    setValidationResult(result);
    setIsPreTtsModalOpen(true);
  };

  const handleConfirmPreTtsProceed = () => {
    setIsPreTtsModalOpen(false);
    onProceedToVoices();
  };

  // Preview Audio
  const handlePreviewTts = (seg: any) => {
    setPreviewingSegId(seg.id);
    const ttsText = seg.tts_text || seg.translated_text || seg.text || '';
    
    if (seg.dirty?.translation || seg.dirty?.tts || seg.tts?.status === 'NEEDS_REGENERATION') {
      setPreviewMessage('Đang phát xem thử với văn bản TTS mới...');
    } else {
      setPreviewMessage(null);
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(ttsText);
      utterance.lang = 'vi-VN';
      utterance.rate = seg.speed || 1.0;
      utterance.onend = () => setPreviewingSegId(null);
      utterance.onerror = () => setPreviewingSegId(null);
      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => setPreviewingSegId(null), 2000);
    }
  };

  // Selected Segment Inspector computation
  const selectedSegment = subtitles.find(s => s.id === selectedSegId) || subtitles[0];
  const selectedTimingValidation = selectedSegment ? TtsValidatorService.validateSegmentTiming(selectedSegment) : null;
  const recommendedSpeedForSelected = selectedTimingValidation
    ? TtsValidatorService.recommendSpeedFactor(selectedTimingValidation.estimatedTtsDuration, selectedTimingValidation.segmentDuration)
    : 1.0;

  // Global Status Bar Metrics
  const totalCount = subtitles.length;
  const translatedCount = subtitles.filter(s => (s.translated_text || '').trim()).length;
  const overflowCount = subtitles.filter(s => !TtsValidatorService.validateSegmentTiming(s).fitsTimeline).length;
  const needsRegenCount = subtitles.filter(s => s.tts?.status === 'NEEDS_REGENERATION' || s.dirty?.translation).length;
  const projectQa = TranslationQaService.checkProjectQa(subtitles);

  const filteredSubtitles = subtitles.filter(seg =>
    (seg.text || seg.original_text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (seg.translated_text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (seg.tts_text || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Detect unknown entities across all segments
  const allTranscriptText = subtitles.map(s => `${s.text || ''} ${s.translated_text || ''}`).join(' ');
  const unknownEntities = PronunciationDictionaryService.detectUnknownEntities(allTranscriptText, dictionary);
  const entityMismatches = PronunciationDictionaryService.detectEntityMismatches(subtitles);

  const handleAddUnknownEntity = (word: string, suggested: string) => {
    const newEntry: DictionaryEntry = {
      id: `proj-${Date.now()}-${Math.random().toString(36).substring(7)}`,
      word,
      pronunciation: suggested,
      language: 'vi',
      source: 'project',
      enabled: true
    };
    const updatedDict = [newEntry, ...dictionary];
    setDictionary(updatedDict);
    PronunciationDictionaryService.saveDictionaryForProject(projectDir, updatedDict);
  };

  const handleFixEntityMismatch = (mismatch: any) => {
    const updated = subtitles.map(s => {
      if (s.id === mismatch.segmentId) {
        const fixedText = (s.text || '').replace(/\bPepper\b/gi, mismatch.suggestedEntity);
        const fixedVietsub = (s.translated_text || '').replace(/\bPepper\b/gi, mismatch.suggestedEntity);
        const autoTts = PronunciationDictionaryService.processText(fixedVietsub, dictionary);
        return {
          ...s,
          text: fixedText,
          original_text: fixedText,
          translated_text: fixedVietsub,
          tts_text: autoTts,
          tts: { ...s.tts, status: 'NEEDS_REGENERATION' },
          dirty: { ...s.dirty, translation: true, tts: true }
        };
      }
      return s;
    });
    setSubtitles(updated);
    pushHistoryState(updated);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%', overflow: 'hidden', minHeight: 0 }}>
      {/* 1. GLOBAL STATUS BAR */}
      <div style={{
        background: '#111318',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        borderRadius: '10px',
        padding: '10px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          {/* Indicator 1: Translation */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe size={15} color={translatedCount === totalCount ? "#10b981" : "#f59e0b"} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TRANSLATION</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: translatedCount === totalCount ? "#10b981" : "#f59e0b" }}>
                {translatedCount === totalCount ? '✓ Completed' : `⚠ ${totalCount - translatedCount} Pending`}
              </span>
            </div>
          </div>

          {/* Indicator 2: Vietsub Review */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Edit3 size={15} color={needsRegenCount === 0 ? "#10b981" : "#06b6d4"} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>VIETSUB REVIEW</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: needsRegenCount === 0 ? "#10b981" : "#06b6d4" }}>
                {needsRegenCount === 0 ? '✓ Completed' : `⚠ ${needsRegenCount} Modified`}
              </span>
            </div>
          </div>

          {/* Indicator 3: Timing */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={15} color={overflowCount === 0 ? "#10b981" : "#ef4444"} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TIMING</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: overflowCount === 0 ? "#10b981" : "#ef4444" }}>
                {overflowCount === 0 ? `✓ All ${totalCount} segments fit` : `⚠ ${overflowCount} Issues | ✓ ${totalCount - overflowCount} Fits`}
              </span>
            </div>
          </div>

          {/* Indicator 4: TTS */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={15} color={needsRegenCount > 0 ? "#f59e0b" : "#10b981"} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TTS PREPARATION</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: needsRegenCount > 0 ? "#f59e0b" : "#10b981" }}>
                {needsRegenCount > 0 ? '⚠ Regeneration Required' : '✓ Ready for TTS'}
              </span>
            </div>
          </div>

          {/* Indicator 5: Translation Style */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe size={15} color="#38bdf8" />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TRANSLATION STYLE</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8' }}>
                🎬 {projectStyle === 'modern' ? 'Hiện đại' : projectStyle === 'ancient' ? 'Cổ trang' : projectStyle === 'time_travel' ? 'Xuyên không' : projectStyle === 'xianxia' ? 'Tiên hiệp' : projectStyle === 'palace' ? 'Cung đấu' : projectStyle === 'cartoon' ? 'Hoạt hình' : projectStyle === 'custom' ? 'Tùy chỉnh' : 'General / Tự động'}
              </span>
            </div>
          </div>
        </div>

        {/* Global Action Tools */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button className="btn-secondary" onClick={handleUndo} disabled={!canUndo} style={{ padding: '4px 10px', fontSize: '11px', opacity: canUndo ? 1 : 0.4 }}>
            <Undo size={12} /> Undo
          </button>
          <button className="btn-secondary" onClick={handleRedo} disabled={!canRedo} style={{ padding: '4px 10px', fontSize: '11px', opacity: canRedo ? 1 : 0.4 }}>
            <Redo size={12} /> Redo
          </button>
          <button className="btn-secondary" onClick={() => setIsDictModalOpen(true)} style={{ padding: '4px 12px', fontSize: '11px', borderColor: 'rgba(99, 102, 241, 0.4)', color: '#818cf8' }}>
            <BookOpen size={12} /> Từ Điển Phát Âm
          </button>
        </div>
      </div>

      {/* UNKNOWN ENTITY REVIEW BANNER */}
      {unknownEntities.length > 0 && (
        <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '8px', padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} color="#f59e0b" />
            <span style={{ fontSize: '12px', color: '#fcd34d', fontWeight: 600 }}>
              ⚠ Phát hiện tên riêng chưa có trong Từ Điển: <strong>"{unknownEntities[0].word}"</strong> (Gợi ý phiên âm: "{unknownEntities[0].suggestedPronunciation}")
            </span>
          </div>
          <button
            className="btn-primary"
            onClick={() => handleAddUnknownEntity(unknownEntities[0].word, unknownEntities[0].suggestedPronunciation)}
            style={{ padding: '4px 12px', fontSize: '11px', background: '#f59e0b', color: '#000', fontWeight: 700, cursor: 'pointer' }}
          >
            Thêm Vào Từ Điển Dự Án
          </button>
        </div>
      )}

      {/* ENTITY MISMATCH REVIEW BANNER */}
      {entityMismatches.length > 0 && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} color="#ef4444" />
            <span style={{ fontSize: '12px', color: '#fca5a5', fontWeight: 600 }}>
              ⚠ Phát hiện lỗi nhận dạng thực thể (STT Error) ở Segment #{entityMismatches[0].segmentId.toString().padStart(3, '0')}: Nhận diện <strong>"{entityMismatches[0].detectedWord}"</strong> (Thực thể dự án: "{entityMismatches[0].suggestedEntity}")
            </span>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn-primary"
              onClick={() => handleFixEntityMismatch(entityMismatches[0])}
              style={{ padding: '4px 12px', fontSize: '11px', background: '#10b981', color: '#000', fontWeight: 700, cursor: 'pointer' }}
            >
              ✓ Sửa Thành {entityMismatches[0].suggestedEntity}
            </button>
          </div>
        </div>
      )}

      {/* TRANSLATION QA REVIEW BANNER (DYNAMIC AI REPAIR) */}
      {projectQa.flaggedCount > 0 && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} color="#ef4444" />
            <span style={{ fontSize: '12px', color: '#fca5a5', fontWeight: 600 }}>
              ⚠ TRANSLATION QA REVIEW ({projectQa.flaggedCount} câu cần xử lý): {projectQa.results.find(r => r.status !== 'PASS')?.issues[0].message} (Segment #{projectQa.results.find(r => r.status !== 'PASS')?.segmentId})
            </span>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn-primary"
              onClick={handleAiRepairAll}
              style={{ padding: '4px 12px', fontSize: '11px', background: 'linear-gradient(135deg, #6366f1, #06b6d4)', color: '#fff', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <Sparkles size={12} /> ✨ AI REPAIR ALL ({projectQa.flaggedCount})
            </button>
          </div>
        </div>
      )}

      {/* 2. MAIN TOOLBAR */}
      <div style={{
        background: '#111318',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        borderRadius: '10px',
        padding: '12px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ position: 'relative', width: '220px' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '9px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="Search transcript..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                background: '#0B0D10',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '6px',
                padding: '6px 10px 6px 28px',
                color: '#fff',
                fontSize: '12px',
                outline: 'none'
              }}
            />
          </div>

          <button className="btn-secondary" onClick={handleFullVietsub} style={{ padding: '6px 12px', fontSize: '12px', borderColor: 'rgba(16, 185, 129, 0.4)', color: '#10b981' }}>
            <Globe size={13} /> VIETSUB TOÀN BỘ
          </button>
          <button className="btn-secondary" onClick={handleFullTtsNormalization} style={{ padding: '6px 12px', fontSize: '12px', borderColor: 'rgba(56, 189, 248, 0.4)', color: '#38bdf8' }}>
            <Volume2 size={13} /> VIỆT HÓA TTS TOÀN BỘ
          </button>
          <button className="btn-secondary" onClick={() => setIsBulkModalOpen(true)} style={{ padding: '6px 12px', fontSize: '12px' }}>
            <Edit3 size={13} /> EDIT ALL
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn-secondary" onClick={loadSubtitles} disabled={isSaving} style={{ padding: '6px 12px', fontSize: '12px' }}>
            <RotateCcw size={12} /> Reset
          </button>
          <button className="btn-primary" onClick={handleSave} disabled={isSaving || !hasChanges} style={{ padding: '6px 14px', fontSize: '12px' }}>
            <Save size={13} /> {isSaving ? 'Saving...' : 'Save Subtitles'}
          </button>
          <button
            className="btn-primary"
            onClick={handleProceedClick}
            disabled={isSaving}
            style={{ padding: '6px 16px', fontSize: '12px', background: 'linear-gradient(135deg, #10b981, #06b6d4)', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            Proceed to Voice Casting <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* 3. MULTI-SELECT BATCH TOOLBAR (Shown when rows selected) */}
      {selectedSegIds.length > 0 && (
        <div style={{ background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)', borderRadius: '8px', padding: '8px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#818cf8' }}>
            Đã chọn {selectedSegIds.length} / {subtitles.length} segments
          </span>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn-secondary" onClick={handleFitSelectedSegments} style={{ padding: '4px 12px', fontSize: '11px', background: '#111318' }}>
              ⚡ Fit Selected to Timeline
            </button>
            <button className="btn-secondary" onClick={() => setSelectedSegIds([])} style={{ padding: '4px 12px', fontSize: '11px', background: '#111318' }}>
              Deselect All
            </button>
          </div>
        </div>
      )}

      {/* 4. WORKSPACE: SEGMENT TABLE + SEGMENT DETAILS INSPECTOR */}
      <div style={{ display: 'flex', gap: '16px', flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* SEGMENT TABLE */}
        <div style={{
          background: '#111318',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          borderRadius: '10px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          overflowY: 'auto',
          flexGrow: 1,
          minWidth: 0,
          minHeight: 0
        }}>
          {/* Table Header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '30px 70px 100px 70px 1fr 1fr 1fr 60px 110px',
            fontSize: '10px',
            color: '#64748b',
            fontWeight: 700,
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            paddingBottom: '8px',
            marginBottom: '8px',
            gap: '8px',
            alignItems: 'center'
          }}>
            <input type="checkbox" checked={selectedSegIds.length === subtitles.length && subtitles.length > 0} onChange={handleSelectAllRows} style={{ cursor: 'pointer' }} />
            <span>SEGMENT</span>
            <span>TIME BOUNDS</span>
            <span>DURATION</span>
            <span>ORIGINAL TEXT</span>
            <span>VIETSUB TEXT</span>
            <span>TTS TEXT</span>
            <span>SPEED</span>
            <span>TTS STATUS</span>
          </div>

          {/* Rows */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flexGrow: 1 }}>
            {filteredSubtitles.map(seg => {
              const isSelected = selectedSegId === seg.id;
              const isBatchSelected = selectedSegIds.includes(seg.id);
              const timingVal = TtsValidatorService.validateSegmentTiming(seg);

              return (
                <div
                  key={seg.id}
                  onClick={() => setSelectedSegId(seg.id)}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '30px 70px 100px 70px 1fr 1fr 1fr 60px 110px',
                    alignItems: 'center',
                    padding: '8px',
                    borderRadius: '6px',
                    background: isSelected ? 'rgba(99, 102, 241, 0.12)' : (isBatchSelected ? 'rgba(99, 102, 241, 0.05)' : 'transparent'),
                    border: '1px solid',
                    borderColor: isSelected ? '#6366f1' : (timingVal.fitsTimeline ? 'transparent' : 'rgba(239, 68, 68, 0.3)'),
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    gap: '8px'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={isBatchSelected}
                    onClick={(e) => handleToggleRowSelect(seg.id, e)}
                    onChange={() => {}}
                    style={{ cursor: 'pointer' }}
                  />

                  <span style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? '#6366f1' : '#94a3b8' }}>
                    #{seg.id.toString().padStart(3, '0')}
                  </span>

                  <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                    {Number(seg.start).toFixed(2)}s - {Number(seg.end).toFixed(2)}s
                  </span>

                  <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8' }}>
                    {timingVal.segmentDuration.toFixed(2)}s
                  </span>

                  <div style={{ fontSize: '12px', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {seg.text || seg.original_text || '(Rỗng)'}
                  </div>

                  <input
                    type="text"
                    value={seg.translated_text || ''}
                    onChange={(e) => handleFieldChange(seg.id, 'translated_text', e.target.value)}
                    style={{
                      background: isSelected ? '#0B0D10' : 'rgba(255,255,255,0.02)',
                      border: '1px solid rgba(255,255,255,0.05)',
                      color: '#fff',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      outline: 'none',
                      width: '100%'
                    }}
                    placeholder="Vietsub..."
                  />

                  <div style={{ position: 'relative', width: '100%' }}>
                    <input
                      type="text"
                      value={seg.tts_text || seg.translated_text || ''}
                      onChange={(e) => handleFieldChange(seg.id, 'tts_text', e.target.value)}
                      style={{
                        background: isSelected ? '#0B0D10' : 'rgba(255,255,255,0.02)',
                        border: '1px solid rgba(16,185,129,0.2)',
                        color: '#38bdf8',
                        padding: '4px 8px',
                        paddingRight: seg.tts_text_override ? '50px' : '8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        outline: 'none',
                        width: '100%'
                      }}
                      placeholder="TTS Text..."
                    />
                    {seg.tts_text_override && (
                      <span style={{ position: 'absolute', right: '4px', top: '5px', fontSize: '9px', fontWeight: 800, color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '1px 4px', borderRadius: '3px' }}>
                        MANUAL
                      </span>
                    )}
                  </div>

                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#f59e0b', textAlign: 'center' }}>
                    {Number(seg.speed || 1.0).toFixed(2)}x
                  </span>

                  <div>
                    {!timingVal.fitsTimeline ? (
                      <span style={{ color: '#ef4444', fontSize: '10px', fontWeight: 700 }}>⚠ Overflow (+{timingVal.overflow}s)</span>
                    ) : seg.tts?.status === 'NEEDS_REGENERATION' ? (
                      <span style={{ color: '#f59e0b', fontSize: '10px', fontWeight: 700 }}>⚠ Needs Regen</span>
                    ) : seg.translated_text ? (
                      <span style={{ color: '#10b981', fontSize: '10px', fontWeight: 700 }}>✓ Ready</span>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '10px', fontWeight: 700 }}>Not Generated</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 5. SEGMENT DETAILS INSPECTOR PANEL */}
        {selectedSegment && selectedTimingValidation && (
          <div style={{
            background: '#111318',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            borderRadius: '10px',
            padding: '18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            width: '320px',
            flexShrink: 0,
            minHeight: 0,
            overflowY: 'auto'
          }}>
            <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#fff' }}>SEGMENT DETAILS</h4>
              <span style={{ fontSize: '12px', fontWeight: 800, color: '#6366f1' }}>#{selectedSegment.id.toString().padStart(3, '0')}</span>
            </div>

            {/* Time bounds */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>START TIME (s)</label>
                <input
                  type="number"
                  step="0.05"
                  value={selectedSegment.start}
                  onChange={e => handleFieldChange(selectedSegment.id, 'start', Number(e.target.value))}
                  style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>END TIME (s)</label>
                <input
                  type="number"
                  step="0.05"
                  value={selectedSegment.end}
                  onChange={e => handleFieldChange(selectedSegment.id, 'end', Number(e.target.value))}
                  style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px' }}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>AVAILABLE DURATION</label>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8', marginTop: '2px' }}>
                {selectedTimingValidation.segmentDuration.toFixed(2)}s
              </div>
            </div>

            {/* Speaker */}
            <div>
              <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>SPEAKER</label>
              <select
                value={selectedSegment.speaker}
                onChange={e => handleFieldChange(selectedSegment.id, 'speaker', e.target.value)}
                style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px' }}
              >
                <option value="Speaker 1">Speaker 1</option>
                <option value="Speaker 2">Speaker 2</option>
                <option value="Speaker 3">Speaker 3</option>
              </select>
            </div>

            {/* Original Text */}
            <div>
              <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>ORIGINAL TEXT</label>
              <div style={{ fontSize: '12px', color: '#cbd5e1', background: '#0B0D10', padding: '8px', borderRadius: '4px', marginTop: '4px', lineHeight: 1.4 }}>
                {selectedSegment.text || selectedSegment.original_text || '(Empty)'}
              </div>
            </div>

            {/* Vietsub Text */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>VIETSUB TEXT (SUBTITLE)</label>
                <button
                  className="btn-secondary"
                  onClick={() => handleSingleAiRepairTranslation(selectedSegment.id)}
                  style={{ fontSize: '9px', padding: '2px 6px', color: '#6366f1', borderColor: 'rgba(99, 102, 241, 0.4)', display: 'flex', alignItems: 'center', gap: '3px', fontWeight: 700 }}
                >
                  <Sparkles size={10} /> ✨ AI SỬA BẢN DỊCH
                </button>
              </div>
              <textarea
                value={selectedSegment.translated_text || ''}
                onChange={e => handleFieldChange(selectedSegment.id, 'translated_text', e.target.value)}
                rows={2}
                style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#fff', padding: '8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px', outline: 'none' }}
              />
              {aiSuggestionMap[selectedSegment.id] && (
                <div style={{ background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)', borderRadius: '4px', padding: '6px 8px', marginTop: '4px' }}>
                  <div style={{ fontSize: '10px', color: '#818cf8', fontWeight: 700, marginBottom: '2px' }}>
                    ✨ AI SUGGESTION (Confidence: {(aiSuggestionMap[selectedSegment.id].confidence * 100).toFixed(0)}%):
                  </div>
                  <div style={{ fontSize: '11px', color: '#e0e7ff', marginBottom: '4px' }}>
                    "{aiSuggestionMap[selectedSegment.id].suggestedTranslation}"
                  </div>
                  <button
                    className="btn-primary"
                    onClick={() => handleApplyAiSuggestion(selectedSegment.id)}
                    style={{ fontSize: '10px', padding: '2px 8px', background: '#6366f1', color: '#fff', fontWeight: 700, borderRadius: '3px', cursor: 'pointer' }}
                  >
                    ✓ ÁP DỤNG BẢN DỊCH AI
                  </button>
                </div>
              )}
            </div>

            {/* TTS Text */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TTS TEXT (PONG PHÁT ÂM)</label>
                {selectedSegment.tts_text_override && (
                  <span style={{ fontSize: '9px', fontWeight: 800, color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '1px 6px', borderRadius: '3px' }}>
                    MANUAL OVERRIDE
                  </span>
                )}
              </div>
              <textarea
                value={selectedSegment.tts_text || selectedSegment.translated_text || ''}
                onChange={e => handleFieldChange(selectedSegment.id, 'tts_text', e.target.value)}
                rows={2}
                style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#38bdf8', padding: '8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px', outline: 'none' }}
              />
              <button
                className="btn-secondary"
                onClick={() => handleSingleAutoGenerateTtsText(selectedSegment.id)}
                style={{ fontSize: '10px', padding: '4px 10px', marginTop: '4px', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.4)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}
              >
                <Sparkles size={11} /> ✨ Auto Generate TTS Text
              </button>
              {(() => {
                const ttsQa = TtsAdaptationEngine.checkTtsQa(selectedSegment.translated_text || '', selectedSegment.tts_text || selectedSegment.translated_text || '');
                return (
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                    <span style={{ fontSize: '9px', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 6px', borderRadius: '3px', fontWeight: 700 }}>
                      🟢 Meaning Preserved
                    </span>
                    <span style={{ fontSize: '9px', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 6px', borderRadius: '3px', fontWeight: 700 }}>
                      🟢 Entity Preserved
                    </span>
                    <span style={{ fontSize: '9px', color: ttsQa.status === 'PASS' ? '#10b981' : '#ef4444', background: ttsQa.status === 'PASS' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)', padding: '2px 6px', borderRadius: '3px', fontWeight: 700 }}>
                      {ttsQa.status === 'PASS' ? '🟢 No Hallucination' : '🔴 Hallucination Rejected'}
                    </span>
                  </div>
                );
              })()}
            </div>

            {/* Speed Factor & Validation */}
            <div style={{ background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', padding: '12px', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700 }}>TTS SPEED</span>
                <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 800, background: 'rgba(16, 185, 129, 0.12)', padding: '2px 8px', borderRadius: '4px' }}>
                  1.00x 🔒 Fixed Natural Speed
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                <span style={{ color: '#94a3b8' }}>TTS Duration Ratio:</span>
                <span style={{ fontWeight: 700, color: selectedTimingValidation.fitsTimeline ? '#38bdf8' : '#ef4444' }}>
                  {selectedTimingValidation.effectiveTtsDuration.toFixed(2)}s / {selectedTimingValidation.segmentDuration.toFixed(2)}s
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                <span style={{ color: '#94a3b8' }}>Status:</span>
                <span style={{ fontWeight: 700, color: selectedTimingValidation.fitsTimeline ? '#10b981' : '#ef4444' }}>
                  {selectedTimingValidation.statusText}
                </span>
              </div>

              {!selectedTimingValidation.fitsTimeline && (
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <span style={{ fontSize: '11px', color: '#ef4444', fontWeight: 600 }}>
                    ⚠ OVERFLOW (+{selectedTimingValidation.overflow.toFixed(2)}s) | Speed: 1.00x 🔒
                  </span>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                    <button
                      className="btn-secondary"
                      onClick={async () => {
                        const timing = TtsValidatorService.validateSegmentTiming(selectedSegment);
                        const result = await TtsAdaptationEngine.optimizeTtsTextForDuration(selectedSegment.tts_text || selectedSegment.translated_text || '', timing.segmentDuration);
                        if (result.fits || result.canFitNaturally) {
                          handleFieldChange(selectedSegment.id, 'tts_text', result.optimizedTtsText);
                        } else {
                          alert(`🔴 CANNOT FIT NATURALLY\nSegment #${selectedSegment.id} quá ngắn để đọc tự nhiên ở tốc độ chuẩn 1.00x.\nĐã tối ưu: "${result.optimizedTtsText}" (${result.estimatedDuration}s / ${timing.segmentDuration}s).`);
                        }
                      }}
                      style={{ fontSize: '10px', padding: '5px 6px', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.4)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '3px' }}
                    >
                      <Sparkles size={11} /> ✨ AI OPTIMIZE TTS
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => {
                        const newEnd = selectedSegment.start + selectedTimingValidation.effectiveTtsDuration + 0.1;
                        handleFieldChange(selectedSegment.id, 'end', Number(newEnd.toFixed(2)));
                      }}
                      style={{ fontSize: '10px', padding: '5px 6px', color: '#38bdf8', borderColor: 'rgba(56, 189, 248, 0.4)', fontWeight: 700 }}
                    >
                      ⏱ Nối Dài Segment
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Inspector Action Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: 'auto' }}>
              <button
                className="btn-secondary"
                onClick={() => handlePreviewTts(selectedSegment)}
                style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                <Play size={13} /> {previewingSegId === selectedSegment.id ? 'Đang đọc...' : 'Preview TTS'}
              </button>
              {previewMessage && (
                <span style={{ fontSize: '10px', color: '#06b6d4', textAlign: 'center' }}>{previewMessage}</span>
              )}
              <button
                className="btn-primary"
                onClick={() => handleFitTtsToSegment(selectedSegment.id)}
                style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', background: 'linear-gradient(135deg, #6366f1, #06b6d4)' }}
              >
                <Zap size={13} /> Fit TTS to Segment
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <PronunciationDictionaryModal
        isOpen={isDictModalOpen}
        entries={dictionary}
        onClose={() => setIsDictModalOpen(false)}
        onSave={(updatedEntries) => {
          setDictionary(updatedEntries);
          PronunciationDictionaryService.saveDictionaryForProject(projectDir, updatedEntries);
        }}
      />

      <BulkVietsubModal
        isOpen={isBulkModalOpen}
        segments={subtitles}
        onClose={() => setIsBulkModalOpen(false)}
        onSave={(updatedSegments) => {
          setSubtitles(updatedSegments);
          setHasChanges(true);
          pushHistoryState(updatedSegments);
        }}
      />

      <PreTtsValidationModal
        isOpen={isPreTtsModalOpen}
        validationResult={validationResult}
        onClose={() => setIsPreTtsModalOpen(false)}
        onConfirmProceed={handleConfirmPreTtsProceed}
      />
    </div>
  );
};
