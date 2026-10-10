export interface QaIssue {
  type: 'MEANING_PRESERVATION' | 'ENTITY_PRESERVATION' | 'PRONOUN_RELATIONSHIP' | 'NUMBER_PRESERVATION' | 'HALLUCINATION_PROTECTION' | 'NATURAL_VIETNAMESE' | 'OUTPUT_INTEGRITY' | 'SEMANTIC_MISMATCH' | 'ENGLISH_LEFTOVER' | 'SUSPICIOUS_GIBBERISH' | 'LITERAL_TRANSLATION_ARTIFACT';
  severity: 'ERROR' | 'WARNING';
  message: string;
}

export interface SegmentQaResult {
  segmentId: number;
  score: number; // 0 - 100
  status: 'PASS' | 'REVIEW' | 'FAIL' | 'ERROR';
  issues: QaIssue[];
}

export class TranslationQaService {
  /**
   * 7-Point Quality Assurance Detector.
   */
  public static checkSegmentQa(seg: any, lockedEntities?: Record<string, string>): SegmentQaResult {
    const orig = (seg.text || seg.original_text || '').trim();
    const trans = (seg.translated_text || seg.translation || '').trim();
    const issues: QaIssue[] = [];

    if (!trans) {
      return {
        segmentId: seg.id,
        score: 0,
        status: 'FAIL',
        issues: [{ type: 'SEMANTIC_MISMATCH', severity: 'ERROR', message: 'Thiếu bản dịch Vietsub' }]
      };
    }

    // 1. Meaning Preservation
    const isActionSentence = /\b(rubbing|sticks|eating|running|cooking|walking|making|building)\b/i.test(orig);
    const isGibberishTrans = /^([A-ZÀÁẢÃẠByeDàp\s\!,]+!+)$/i.test(trans) || trans.includes('Dàp-dàp') || trans.includes('Byé');
    if (isActionSentence && isGibberishTrans) {
      issues.push({
        type: 'MEANING_PRESERVATION',
        severity: 'ERROR',
        message: 'Lỗi nghĩa: Câu mô tả hành động bị phát sinh từ vô nghĩa'
      });
    }

    // 2. Entity Preservation & Relationship Hallucination Check
    if (lockedEntities) {
      for (const [zh, vi] of Object.entries(lockedEntities)) {
        if (orig.includes(zh) && !trans.includes(vi)) {
          issues.push({
            type: 'ENTITY_PRESERVATION',
            severity: 'ERROR',
            message: `Vi phạm Locked Entity: Thực thể '${zh}' chưa được dịch đúng thành '${vi}'`
          });
        }
      }
    }

    const transFamilyHallucinations = trans.match(/\b(Dì|Chú|Bác|Cô|Thím|Pig|Heo)\b/gi);
    if (transFamilyHallucinations && !/[阿姨姑姑舅舅叔叔猪]/.test(orig)) {
      issues.push({
        type: 'HALLUCINATION_PROTECTION',
        severity: 'ERROR',
        message: `Ảo giác quan hệ nhân vật: Tự bịa từ xưng hô (${transFamilyHallucinations.join(', ')}) không có trong câu gốc`
      });
    }

    // 3. Pronoun & Relationship
    const unadaptedPronouns = trans.match(/\b(I|you|he|she|they|we|me|him|her)\b/gi);
    if (unadaptedPronouns) {
      issues.push({
        type: 'PRONOUN_RELATIONSHIP',
        severity: 'WARNING',
        message: `Đại từ tiếng Anh chưa được chuyển ngữ: "${unadaptedPronouns.join(', ')}"`
      });
    }

    // 4. Number Preservation
    const origNumbers = (orig.match(/\d+/g) || []).sort().join(',');
    const transNumbers = (trans.match(/\d+/g) || []).sort().join(',');
    if (origNumbers && origNumbers !== transNumbers) {
      issues.push({
        type: 'NUMBER_PRESERVATION',
        severity: 'ERROR',
        message: `Sai lệch con số: Bản gốc (${origNumbers}) vs Vietsub (${transNumbers || 'Không có'})`
      });
    }

    // 5. Hallucination Protection (Chinese character remnants)
    if (/[\u4e00-\u9fff]/.test(trans)) {
      issues.push({
        type: 'HALLUCINATION_PROTECTION',
        severity: 'ERROR',
        message: 'Lỗi ảo giác: Còn sót ký tự tiếng Trung trong bản dịch Tiếng Việt'
      });
    }

    // 6. Natural Vietnamese
    if (/(\b[\w\s]{2,20}\b)(?:\s+\1){2,}/i.test(trans)) {
      issues.push({
        type: 'NATURAL_VIETNAMESE',
        severity: 'WARNING',
        message: 'Lặp từ bất thường trong câu Vietsub'
      });
    }

    // 7. Output Integrity Check
    const integrityLeaks = [];
    if (/\b(this translation|note:|in vietnamese|explanation|translates to)\b/i.test(trans)) {
      integrityLeaks.push('Chứa câu giải thích tiếng Anh của AI');
    }
    if (/\*\*|```|\{|\}/.test(trans)) {
      integrityLeaks.push('Dính định dạng Markdown hoặc rác JSON');
    }
    if (/\b(system:|rules:|instruction|prompt:)\b/i.test(trans)) {
      integrityLeaks.push('Rò rỉ câu lệnh hệ thống (Instruction leakage)');
    }
    if (trans.includes('\n') || /Option 1|Option 2|Bản 1|Bản 2/i.test(trans)) {
      integrityLeaks.push('Trả về nhiều phương án dịch');
    }

    if (integrityLeaks.length > 0) {
      issues.push({
        type: 'OUTPUT_INTEGRITY',
        severity: 'ERROR',
        message: `Lỗi tính toàn vẹn đầu ra: ${integrityLeaks.join('; ')}`
      });
    }

    // Calculate Quality Score
    let score = 100;
    for (const issue of issues) {
      if (issue.severity === 'ERROR') score -= 30;
      else if (issue.severity === 'WARNING') score -= 15;
    }
    score = Math.max(0, score);

    const status: 'PASS' | 'REVIEW' | 'FAIL' = anyError(issues)
      ? 'FAIL'
      : (score >= 85 ? 'PASS' : 'REVIEW');

    return {
      segmentId: seg.id,
      score,
      status,
      issues
    };
  }

  public static checkProjectQa(segments: any[], lockedEntities?: Record<string, string>): {
    totalSegments: number;
    passedCount: number;
    flaggedCount: number;
    results: SegmentQaResult[];
  } {
    const results = segments.map(s => this.checkSegmentQa(s, lockedEntities));
    const passedCount = results.filter(r => r.status === 'PASS').length;
    const flaggedCount = results.length - passedCount;

    return {
      totalSegments: segments.length,
      passedCount,
      flaggedCount,
      results
    };
  }
}

function anyError(issues: QaIssue[]): boolean {
  return issues.some(i => i.severity === 'ERROR');
}
