import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Split, 
  Combine, 
  Lock, 
  Unlock, 
  Play, 
  RefreshCw, 
  Check, 
  User, 
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  speaker: string;
  locked?: boolean;
}

interface TranscriptEditorProps {
  projectDir?: string | null;
  onProceedToTranslation?: () => void;
}

export const TranscriptEditor: React.FC<TranscriptEditorProps> = ({
  projectDir,
  onProceedToTranslation
}) => {
  const [segments, setSegments] = useState<TranscriptSegment[]>([
    { id: 1, start: 1.2, end: 4.96, text: "Hello everyone, welcome to our travel documentary.", speaker: "Narrator", locked: false },
    { id: 2, start: 6.12, end: 9.16, text: "Today we will explore the breathtaking scenery of Da Lat.", speaker: "Narrator", locked: false },
    { id: 3, start: 10.0, end: 14.2, text: "The weather here is cool and refreshing all year round.", speaker: "A Lang", locked: true },
    { id: 4, start: 15.1, end: 19.5, text: "Let's take a look at the famous flower garden.", speaker: "B Lang", locked: false }
  ]);
  const [selectedSegmentId, setSelectedSegmentId] = useState<number | null>(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [speakerFilter, setSpeakerFilter] = useState<string>('ALL');

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.readSubtitles(projectDir).then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setSegments(data.map(s => ({
            id: s.id,
            start: Number(s.start || 0),
            end: Number(s.end || 0),
            text: s.text || '',
            speaker: s.speaker || 'Narrator',
            locked: false
          })));
        }
      }).catch(e => console.error('Failed to read transcript:', e));
    }
  }, [projectDir]);

  const formatTimecode = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
  };

  const handleTextChange = (id: number, newText: string) => {
    setSegments(prev => prev.map(s => s.id === id ? { ...s, text: newText } : s));
  };

  const toggleLock = (id: number) => {
    setSegments(prev => prev.map(s => s.id === id ? { ...s, locked: !s.locked } : s));
  };

  const handleSplitSegment = (id: number) => {
    const seg = segments.find(s => s.id === id);
    if (!seg) return;
    const mid = seg.start + (seg.end - seg.start) / 2;
    const words = seg.text.split(' ');
    const half = Math.ceil(words.length / 2);
    
    const newSeg1: TranscriptSegment = { ...seg, end: mid, text: words.slice(0, half).join(' ') };
    const newSeg2: TranscriptSegment = { id: Date.now(), start: mid, end: seg.end, text: words.slice(half).join(' '), speaker: seg.speaker };

    const idx = segments.findIndex(s => s.id === id);
    const updated = [...segments];
    updated.splice(idx, 1, newSeg1, newSeg2);
    setSegments(updated);
  };

  const filteredSegments = segments.filter(s => {
    const matchesSearch = s.text.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSpeaker = speakerFilter === 'ALL' || s.speaker === speakerFilter;
    return matchesSearch && matchesSpeaker;
  });

  const getSpeakerBadgeColor = (speaker: string) => {
    switch (speaker) {
      case 'Narrator':
        return 'bg-[#00f0ff]/15 text-[#00f0ff] border-[#00f0ff]/30';
      case 'A Lang':
        return 'bg-[#ff007f]/15 text-[#ff007f] border-[#ff007f]/30';
      case 'B Lang':
        return 'bg-[#7928ca]/15 text-[#b075ff] border-[#7928ca]/30';
      default:
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER TOOLBAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#00f0ff]/10 text-[#00f0ff] flex items-center justify-center border border-[#00f0ff]/20">
            <FileText size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Transcript Editor (Whisper STT)
            </h2>
            <p className="text-xs text-slate-400">
              Review and edit original timestamps, text segments, and speaker assignments.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => alert('Regenerating Whispr STT Transcript...')}
            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition-all"
          >
            <RefreshCw size={13} /> Regenerate STT
          </button>
          <button
            onClick={onProceedToTranslation}
            className="px-4 py-1.5 rounded-lg bg-[#00f0ff] hover:bg-[#00f0ff]/80 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-[#00f0ff]/20 transition-all"
          >
            <Sparkles size={14} /> Proceed to Translation ➔
          </button>
        </div>
      </div>

      {/* MAIN CONTAINER: SEARCH & SEGMENT LIST */}
      <div className="flex-1 bg-[#111318] rounded-xl border border-white/5 flex flex-col overflow-hidden shadow-sm">
        {/* FILTER BAR */}
        <div className="p-3 border-b border-white/5 bg-black/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 relative max-w-xs w-full">
            <Search size={14} className="absolute left-3 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search transcript text..."
              className="w-full bg-[#0b0d10] border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#00f0ff]"
            />
          </div>

          <div className="flex items-center gap-3">
            <span className="text-slate-400 font-semibold">Filter Speaker:</span>
            <select
              value={speakerFilter}
              onChange={e => setSpeakerFilter(e.target.value)}
              className="bg-[#0b0d10] border border-white/10 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Speakers</option>
              <option value="Narrator">Narrator</option>
              <option value="A Lang">A Lang</option>
              <option value="B Lang">B Lang</option>
            </select>
          </div>
        </div>

        {/* SEGMENTS LIST */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
          {filteredSegments.map((seg, idx) => {
            const isSelected = selectedSegmentId === seg.id;
            return (
              <div
                key={seg.id}
                onClick={() => setSelectedSegmentId(seg.id)}
                className={`p-3 rounded-lg border transition-all ${
                  isSelected
                    ? 'bg-[#00f0ff]/5 border-[#00f0ff]/40 shadow-sm'
                    : 'bg-[#0b0d10]/60 hover:bg-[#0b0d10] border-white/5'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">
                      #{idx + 1}
                    </span>
                    <span className="text-xs font-mono text-[#00f0ff] font-semibold">
                      {formatTimecode(seg.start)} ➔ {formatTimecode(seg.end)}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getSpeakerBadgeColor(seg.speaker)}`}>
                      <User size={10} className="inline mr-1" />
                      {seg.speaker}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleSplitSegment(seg.id); }}
                      className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white"
                      title="Split Segment at cursor"
                    >
                      <Split size={13} />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleLock(seg.id); }}
                      className={`p-1 rounded transition-colors ${
                        seg.locked ? 'bg-amber-500/20 text-amber-300' : 'bg-white/5 text-slate-400 hover:text-white'
                      }`}
                      title={seg.locked ? 'Unlock Segment' : 'Lock Segment'}
                    >
                      {seg.locked ? <Lock size={13} /> : <Unlock size={13} />}
                    </button>
                  </div>
                </div>

                <textarea
                  value={seg.text}
                  onChange={e => handleTextChange(seg.id, e.target.value)}
                  disabled={seg.locked}
                  rows={2}
                  className="w-full bg-black/40 border border-white/5 rounded-md p-2 text-xs text-slate-200 focus:outline-none focus:border-[#00f0ff]/50 disabled:opacity-60 resize-none font-sans"
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
