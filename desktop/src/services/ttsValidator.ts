export interface SegmentValidationResult {
  segmentId: number;
  segmentDuration: number;
  estimatedTtsDuration: number;
  actualTtsDuration?: number;
  effectiveTtsDuration: number;
  requiredSpeedFactor: number;
  exceedsSafeSpeedLimit: boolean;
  overflow: number;
  fitsTimeline: boolean;
  statusText: string;
  hasTranslation: boolean;
  hasTtsText: boolean;
  warning: string | null;
  recommendedStrategy: 'FIT' | 'AI_TEXT_ADAPTATION' | 'AI_TEXT_COMPRESSION' | 'HUMAN_REVIEW' | 'ACCEPT_OVERFLOW';
}

export interface ChecklistItem {
  id: string;
  label: string;
  passed: boolean;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  details?: string;
}

export interface PreTtsValidationResult {
  canProceed: boolean;
  checklist: ChecklistItem[];
  overflowCount: number;
  warningCount: number;
  errorCount: number;
}

export class TtsValidatorService {
  public static FIXED_TTS_SPEED = 1.00;

  /**
   * Estimates TTS speech duration for Vietnamese text at FIXED 1.00x speed.
   * Standard Vietnamese speech rate: ~14.5 characters per second + 0.2s base pause.
   */
  public static estimateTtsDuration(ttsText: string, _speedFactor: number = 1.0): number {
    if (!ttsText || !ttsText.trim()) return 0.0;
    const clean = ttsText.trim();
    const charCount = clean.length;
    const wordCount = clean.split(/\s+/).length;

    const baseDuration = Math.max(0.5, (charCount / 14.5) + (wordCount * 0.05) + 0.2);
    // Speed is strictly fixed to 1.00x
    return Number(baseDuration.toFixed(2));
  }

  /**
   * Validates a single segment's timing bounds vs estimated/actual TTS duration at FIXED 1.00x speed.
   */
  public static validateSegmentTiming(seg: any): SegmentValidationResult {
    const start = Number(seg.start || seg.startTime || 0);
    const end = Number(seg.end || seg.endTime || 0);
    const segmentDuration = Math.max(0.1, end - start);

    const ttsText = seg.tts_text || seg.ttsText || seg.translated_text || seg.text || '';
    const estimatedTtsDuration = this.estimateTtsDuration(ttsText, 1.00);
    const actualTtsDuration = seg.tts?.duration;

    const effectiveTtsDuration = actualTtsDuration !== undefined ? actualTtsDuration : estimatedTtsDuration;
    const overflow = Number(Math.max(0, effectiveTtsDuration - segmentDuration).toFixed(2));

    const fitsTimeline = overflow <= 0.05;
    const hasTranslation = Boolean((seg.translated_text || seg.translation || '').trim());
    const hasTtsText = Boolean(ttsText.trim());

    let warning: string | null = null;
    let statusText = '✓ Fits segment (1.00x Fixed Speed)';
    let recommendedStrategy: 'FIT' | 'AI_TEXT_ADAPTATION' | 'AI_TEXT_COMPRESSION' | 'HUMAN_REVIEW' | 'ACCEPT_OVERFLOW' = 'FIT';

    if (!fitsTimeline) {
      statusText = `⚠ TTS exceeds segment (+${overflow.toFixed(2)}s)`;
      if (overflow > 1.5) {
        warning = `Overflow (+${overflow.toFixed(2)}s) requires Human Review or AI Compression`;
        recommendedStrategy = 'HUMAN_REVIEW';
      } else {
        warning = `Overflow (+${overflow.toFixed(2)}s) - Recommended AI Text Adaptation`;
        recommendedStrategy = 'AI_TEXT_COMPRESSION';
      }
    }

    return {
      segmentId: seg.id,
      segmentDuration,
      estimatedTtsDuration,
      actualTtsDuration,
      effectiveTtsDuration,
      requiredSpeedFactor: 1.00,
      exceedsSafeSpeedLimit: false,
      overflow,
      fitsTimeline,
      statusText,
      hasTranslation,
      hasTtsText,
      warning,
      recommendedStrategy
    };
  }

  /**
   * Always returns FIXED 1.00x speed factor according to system architectural policy.
   */
  public static recommendSpeedFactor(_estimatedDuration: number, _segmentDuration: number): number {
    return 1.00;
  }

  /**
   * Validates entire project segments before triggering TTS.
   */
  public static validatePreTtsChecklist(segments: any[]): PreTtsValidationResult {
    const checklist: ChecklistItem[] = [];

    // 1. All segments have translated text
    const missingTranslationCount = segments.filter(s => !(s.translated_text || s.translation || '').trim()).length;
    checklist.push({
      id: 'translation',
      label: 'All segments have translated text (Vietsub)',
      passed: missingTranslationCount === 0,
      severity: 'ERROR',
      details: missingTranslationCount > 0 ? `${missingTranslationCount} segment(s) missing translation` : undefined
    });

    // 2. All segments have TTS text
    const missingTtsTextCount = segments.filter(s => !(s.tts_text || s.translated_text || s.text || '').trim()).length;
    checklist.push({
      id: 'tts_text',
      label: 'All segments have TTS text prepared',
      passed: missingTtsTextCount === 0,
      severity: 'ERROR',
      details: missingTtsTextCount > 0 ? `${missingTtsTextCount} segment(s) missing TTS text` : undefined
    });

    // 3. Timeline bounds validity
    const invalidTimelineCount = segments.filter(s => Number(s.end || 0) <= Number(s.start || 0)).length;
    checklist.push({
      id: 'timeline_bounds',
      label: 'Timeline bounds valid (End Time > Start Time)',
      passed: invalidTimelineCount === 0,
      severity: 'ERROR',
      details: invalidTimelineCount > 0 ? `${invalidTimelineCount} segment(s) have invalid timestamps` : undefined
    });

    // 4. Speaker assignment
    const missingSpeakerCount = segments.filter(s => !(s.speaker || '').trim()).length;
    checklist.push({
      id: 'speakers',
      label: 'Speakers assigned to all segments',
      passed: missingSpeakerCount === 0,
      severity: 'WARNING',
      details: missingSpeakerCount > 0 ? `${missingSpeakerCount} segment(s) default to Speaker 1` : undefined
    });

    // 5. Overflow check (evaluated at FIXED 1.00x speed)
    const validations = segments.map(s => this.validateSegmentTiming(s));
    const overflowSegments = validations.filter(v => !v.fitsTimeline);
    checklist.push({
      id: 'duration_overflow',
      label: 'TTS Duration fits available segment windows (1.00x Fixed Speed)',
      passed: overflowSegments.length === 0,
      severity: 'WARNING',
      details: overflowSegments.length > 0 ? `${overflowSegments.length} segment(s) exceed available duration` : undefined
    });

    // 6. Stale audio / regeneration needed check
    const needsRegenerationCount = segments.filter(s => s.tts?.status === 'NEEDS_REGENERATION' || s.dirty?.translation || s.dirty?.tts).length;
    checklist.push({
      id: 'stale_audio',
      label: 'No stale audio requiring regeneration',
      passed: needsRegenerationCount === 0,
      severity: 'WARNING',
      details: needsRegenerationCount > 0 ? `${needsRegenerationCount} segment(s) marked for regeneration` : undefined
    });

    const errorCount = checklist.filter(c => !c.passed && c.severity === 'ERROR').length;
    const warningCount = checklist.filter(c => !c.passed && c.severity === 'WARNING').length;
    const overflowCount = overflowSegments.length;

    return {
      canProceed: errorCount === 0,
      checklist,
      overflowCount,
      warningCount,
      errorCount
    };
  }
}
