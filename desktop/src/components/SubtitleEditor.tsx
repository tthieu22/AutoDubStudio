import React, { useState, useEffect, useRef } from 'react';
import { Globe, Clock, Zap, Undo, Redo, Sparkles } from 'lucide-react';
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

import { SubtitleToolbar } from './subtitle/SubtitleToolbar';
import { SubtitleItemCard } from './subtitle/SubtitleItemCard';
import { SubtitleDetailPanel } from './subtitle/SubtitleDetailPanel';

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
  const [projectStyle, setProjectStyle] = useState<string>('general');
  const [aiSuggestionMap, setAiSuggestionMap] = useState<Record<number, any>>({});

  useEffect(() => {
    if (activeTab === 'subtitles' || !activeTab) {
      loadSubtitles();
      const loadedDict = PronunciationDictionaryService.getDictionaryForProject(projectDir);
      setDictionary(loadedDict);
    }
  }, [projectDir, activeTab]);

  const pushHistoryState = (newSubtitles: any[]) => {
    const clone = JSON.parse(JSON.stringify(newSubtitles));
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
    alert(`✓ Đã Việt hóa TTS xong cho ${subtitles.length} segments!\n- Tự động tạo: ${autoGenCount} câu\n- Giữ nguyên tùy chỉnh tay: ${manualPreservedCount} câu`);
  };

  const handleSingleAutoGenerateTtsText = async (segId: number) => {
    const seg = subtitles.find(s => s.id === segId);
    if (!seg) return;

    const sourceVietsub = (seg.translated_text || seg.text || '').trim();
    let candidateTts = PronunciationDictionaryService.processText(sourceVietsub, dictionary);

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
  };

  const handleSingleAiRepairTranslation = async (segId: number) => {
    const seg = subtitles.find(s => s.id === segId);
    if (!seg) return;

    const qaRes = TranslationQaService.checkSegmentQa(seg);
    const repairRes = await TranslationRepairService.repairSegmentAi(seg, qaRes.issues);

    setAiSuggestionMap(prev => ({ ...prev, [segId]: repairRes }));

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

  const handleFitTtsToSegment = async (segId: number) => {
    const seg = subtitles.find(s => s.id === segId);
    if (!seg) return;

    const timing = TtsValidatorService.validateSegmentTiming(seg);
    const currentTts = (seg.tts_text || seg.translated_text || '').trim();

    const result = await TtsAdaptationEngine.optimizeTtsTextForDuration(currentTts, timing.segmentDuration);
    let updatedSeg = { ...seg };

    if (result.fits || result.canFitNaturally) {
      updatedSeg.tts_text = result.optimizedTtsText;
      updatedSeg.dirty = { ...seg.dirty, tts: true };
      updatedSeg.tts = { ...seg.tts, status: 'NEEDS_REGENERATION' };
    } else {
      const newEnd = Number((seg.start + timing.effectiveTtsDuration + 0.1).toFixed(2));
      updatedSeg.end = newEnd;
      updatedSeg.dirty = { ...seg.dirty, timing: true };
    }

    const updated = subtitles.map(s => s.id === segId ? updatedSeg : s);
    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);

    const clipId = `clip-sub-${segId}`;
    const targetClip = editorStore.getComposition().clips.find(c => c.id === clipId);
    if (targetClip) {
      editorStore.updateClip(clipId, { duration: Math.max(0.2, updatedSeg.end - targetClip.startTime) });
    }

    await PythonEngineService.writeSubtitles(projectDir, updated);
  };

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

  const handleProceedClick = () => {
    const result = TtsValidatorService.validatePreTtsChecklist(subtitles);
    setValidationResult(result);
    setIsPreTtsModalOpen(true);
  };

  const handleConfirmPreTtsProceed = () => {
    setIsPreTtsModalOpen(false);
    onProceedToVoices();
  };

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

  const selectedSegment = subtitles.find(s => s.id === selectedSegId) || subtitles[0];
  const selectedTimingValidation = selectedSegment ? TtsValidatorService.validateSegmentTiming(selectedSegment) : null;

  const totalCount = subtitles.length;
  const translatedCount = subtitles.filter(s => (s.translated_text || '').trim()).length;
  const overflowCount = subtitles.filter(s => !TtsValidatorService.validateSegmentTiming(s).fitsTimeline).length;
  const needsRegenCount = subtitles.filter(s => s.tts?.status === 'NEEDS_REGENERATION' || s.dirty?.translation).length;

  const filteredSubtitles = subtitles.filter(seg =>
    (seg.text || seg.original_text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (seg.translated_text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (seg.tts_text || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleApplyDictionaryToSubtitles = (updatedEntries: DictionaryEntry[], targetMode: 'tts' | 'both' = 'tts') => {
    setDictionary(updatedEntries);
    PronunciationDictionaryService.saveDictionaryForProject(projectDir, updatedEntries);

    const updated = subtitles.map(seg => {
      const currentVietsub = seg.translated_text || seg.translation || '';
      const newTts = PronunciationDictionaryService.processText(currentVietsub, updatedEntries);
      const newVietsub = targetMode === 'both'
        ? PronunciationDictionaryService.processText(currentVietsub, updatedEntries)
        : currentVietsub;

      return {
        ...seg,
        translated_text: newVietsub,
        tts_text: newTts,
        tts: { ...seg.tts, status: 'NEEDS_REGENERATION' },
        dirty: {
          ...seg.dirty,
          translation: targetMode === 'both' ? true : seg.dirty?.translation,
          tts: true
        }
      };
    });

    setSubtitles(updated);
    setHasChanges(true);
    pushHistoryState(updated);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%', overflow: 'hidden', minHeight: 0 }}>
      {/* TOOLBAR */}
      <SubtitleToolbar
        projectStyle={projectStyle}
        searchQuery={searchQuery}
        hasChanges={hasChanges}
        isSaving={isSaving}
        isTranslating={isTranslating}
        canUndo={canUndo}
        canRedo={canRedo}
        subtitlesCount={subtitles.length}
        onSearchChange={setSearchQuery}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onOpenDictModal={() => setIsDictModalOpen(true)}
        onOpenBulkModal={() => setIsBulkModalOpen(true)}
        onOpenPreTtsModal={handleProceedClick}
        onAiRepairAll={handleAiRepairAll}
        onAutoPrepareTtsText={handleFullTtsNormalization}
        onSaveSubtitles={handleSave}
        onProceedToVoices={onProceedToVoices}
      />

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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe size={15} color={translatedCount === totalCount ? "#10b981" : "#f59e0b"} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>VIETSUB REVIEW</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: translatedCount === totalCount ? "#10b981" : "#f59e0b" }}>
                {translatedCount === totalCount ? '✓ Completed' : `⚠ ${totalCount - translatedCount} Pending`}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={15} color={overflowCount > 0 ? "#f59e0b" : "#10b981"} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TIMING</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: overflowCount > 0 ? "#f59e0b" : "#10b981" }}>
                {overflowCount > 0 ? `⚠ ${overflowCount} Issues` : `✓ ${totalCount} Fits`}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={15} color={needsRegenCount > 0 ? "#f59e0b" : "#10b981"} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TTS PREPARATION</span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: needsRegenCount > 0 ? "#f59e0b" : "#10b981" }}>
                {needsRegenCount > 0 ? '⚠ Regeneration Required' : '✓ Ready for TTS'}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button className="btn-secondary" onClick={handleUndo} disabled={!canUndo} style={{ padding: '4px 10px', fontSize: '11px', opacity: canUndo ? 1 : 0.4 }}>
            <Undo size={12} /> Undo
          </button>
          <button className="btn-secondary" onClick={handleRedo} disabled={!canRedo} style={{ padding: '4px 10px', fontSize: '11px', opacity: canRedo ? 1 : 0.4 }}>
            <Redo size={12} /> Redo
          </button>
        </div>
      </div>

      {/* MULTI-SELECT BATCH TOOLBAR */}
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

      {/* WORKSPACE: SEGMENT TABLE + DETAILS INSPECTOR */}
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
            {filteredSubtitles.map(seg => (
              <SubtitleItemCard
                key={seg.id}
                seg={seg}
                isSelected={selectedSegId === seg.id}
                isBatchSelected={selectedSegIds.includes(seg.id)}
                onSelectSegment={setSelectedSegId}
                onToggleRowSelect={handleToggleRowSelect}
                onFieldChange={handleFieldChange}
              />
            ))}
          </div>
        </div>

        {/* DETAILS INSPECTOR PANEL */}
        {selectedSegment && selectedTimingValidation && (
          <SubtitleDetailPanel
            selectedSegment={selectedSegment}
            selectedTimingValidation={selectedTimingValidation}
            aiSuggestionMap={aiSuggestionMap}
            previewingSegId={previewingSegId}
            previewMessage={previewMessage}
            onFieldChange={handleFieldChange}
            onSingleAiRepairTranslation={handleSingleAiRepairTranslation}
            onApplyAiSuggestion={handleApplyAiSuggestion}
            onSingleAutoGenerateTtsText={handleSingleAutoGenerateTtsText}
            onPreviewTts={handlePreviewTts}
            onFitTtsToSegment={handleFitTtsToSegment}
          />
        )}
      </div>

      {/* Modals */}
      <PronunciationDictionaryModal
        isOpen={isDictModalOpen}
        entries={dictionary}
        subtitles={subtitles}
        onClose={() => setIsDictModalOpen(false)}
        onSave={(updatedEntries) => {
          setDictionary(updatedEntries);
          PronunciationDictionaryService.saveDictionaryForProject(projectDir, updatedEntries);
        }}
        onApplyToSubtitles={handleApplyDictionaryToSubtitles}
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
