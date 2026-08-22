import React, { useState, useEffect } from 'react';
import { Save, RotateCcw, Clock, Sparkles, User, AlertCircle, Search } from 'lucide-react';
import { PythonEngineService } from '../services/pythonEngine';
import { editorStore } from '../editor/state/editorStore';

interface SubtitleEditorProps {
  projectDir: string;
}

export const SubtitleEditor: React.FC<SubtitleEditorProps> = ({ projectDir }) => {
  const [subtitles, setSubtitles] = useState<any[]>([]);
  const [selectedSegId, setSelectedSegId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadSubtitles();
  }, [projectDir]);

  const loadSubtitles = async () => {
    try {
      const data = await PythonEngineService.readSubtitles(projectDir);
      setSubtitles(data);
      if (data.length > 0) setSelectedSegId(data[0].id);
      setHasChanges(false);
    } catch (err) {
      console.error('Failed to load subtitles:', err);
    }
  };

  const handleFieldChange = (id: number, field: string, value: any) => {
    const updated = subtitles.map(s => {
      if (s.id === id) {
        return { ...s, [field]: value };
      }
      return s;
    });
    setSubtitles(updated);
    setHasChanges(true);

    // Sync directly to timeline subtitle clip
    const currentComp = editorStore.getComposition();
    const clipId = `clip-sub-${id}`;
    const targetClip = currentComp.clips.find(c => c.id === clipId);
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
      alert(`Save failed: ${err}`);
    } finally {
      setIsSaving(false);
    }
  };

  const filteredSubtitles = subtitles.filter(seg => 
    (seg.text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (seg.translated_text || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', overflow: 'hidden' }}>
      {/* 1. CONTROL HEADER */}
      <div 
        style={{ 
          background: '#111318', 
          border: '1px solid rgba(255, 255, 255, 0.05)', 
          borderRadius: '10px', 
          padding: '12px 20px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          flexShrink: 0
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles color="#6366f1" size={18} />
          <div>
            <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#fff' }}>Transcript & Subtitle Editor</h3>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Edit content scripts, adjust timelines, and speed factors</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Search */}
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

          <button className="btn-secondary" onClick={loadSubtitles} disabled={isSaving} style={{ padding: '6px 12px', fontSize: '12px' }}>
            <RotateCcw size={12} /> Reset
          </button>
          <button className="btn-primary" onClick={handleSave} disabled={isSaving || !hasChanges} style={{ padding: '6px 14px', fontSize: '12px' }}>
            <Save size={13} /> {isSaving ? 'Saving...' : 'Save Subtitles'}
          </button>
        </div>
      </div>

      {/* 2. DUAL-PANEL WORKSPACE */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '16px', flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* TRANSCRIPT VIEW PANEL */}
        <div 
          style={{ 
            background: '#111318', 
            border: '1px solid rgba(255, 255, 255, 0.05)', 
            borderRadius: '10px', 
            padding: '16px', 
            display: 'flex', 
            flexDirection: 'column', 
            overflowY: 'auto' 
          }}
        >
          {/* Table Header */}
          <div 
            style={{ 
              display: 'grid', 
              gridTemplateColumns: '80px 100px 1fr 1fr', 
              fontSize: '11px', 
              color: '#64748b', 
              fontWeight: 700, 
              borderBottom: '1px solid rgba(255, 255, 255, 0.05)', 
              paddingBottom: '8px',
              marginBottom: '8px' 
            }}
          >
            <span>SEGMENT</span>
            <span>TIME BOUNDS</span>
            <span>ORIGINAL TEXT</span>
            <span>TRANSLATED TEXT</span>
          </div>

          {/* Rows */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flexGrow: 1 }}>
            {filteredSubtitles.map(seg => {
              const isSelected = selectedSegId === seg.id;
              return (
                <div
                  key={seg.id}
                  onClick={() => setSelectedSegId(seg.id)}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '80px 100px 1fr 1fr',
                    alignItems: 'center',
                    padding: '8px',
                    borderRadius: '6px',
                    background: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'transparent',
                    border: '1px solid',
                    borderColor: isSelected ? 'rgba(99, 102, 241, 0.3)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    gap: '12px'
                  }}
                >
                  {/* Segment ID */}
                  <span style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? '#6366f1' : '#94a3b8' }}>
                    #{seg.id.toString().padStart(3, '0')}
                  </span>

                  {/* Timestamps */}
                  <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                    {seg.start.toFixed(2)}s - {seg.end.toFixed(2)}s
                  </span>

                  {/* Original Text */}
                  <div style={{ fontSize: '12px', color: '#cbd5e1', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {seg.text || seg.original_text || '(Empty)'}
                  </div>

                  {/* Inline Translation input */}
                  <input
                    type="text"
                    value={seg.translated_text || ''}
                    onChange={(e) => handleFieldChange(seg.id, 'translated_text', e.target.value)}
                    style={{
                      background: isSelected ? '#0B0D10' : 'rgba(255,255,255,0.02)',
                      border: '1px solid',
                      borderColor: isSelected ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      outline: 'none',
                      width: '100%'
                    }}
                    placeholder="Enter translation..."
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* TRANSCRIPT SEGMENT INSPECTOR */}
        <div 
          style={{ 
            background: '#111318', 
            border: '1px solid rgba(255, 255, 255, 0.05)', 
            borderRadius: '10px', 
            padding: '20px', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px' 
          }}
        >
          <div style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '12px' }}>
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Segment Details
            </span>
            <h4 style={{ margin: '4px 0 0 0', fontSize: '15px', fontWeight: 700, color: '#fff' }}>
              Segment #{selectedSegId !== null ? selectedSegId.toString().padStart(3, '0') : '-'}
            </h4>
          </div>

          {selectedSegId !== null ? (() => {
            const activeSeg = subtitles.find(s => s.id === selectedSegId) || {};
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', flexGrow: 1 }}>
                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>START TIME (SECONDS)</label>
                  <input
                    type="number"
                    step="0.05"
                    value={activeSeg.start || 0}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'start', parseFloat(e.target.value))}
                    style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', color: '#fff', padding: '6px 10px', borderRadius: '6px', outline: 'none', fontSize: '12px' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>END TIME (SECONDS)</label>
                  <input
                    type="number"
                    step="0.05"
                    value={activeSeg.end || 0}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'end', parseFloat(e.target.value))}
                    style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', color: '#fff', padding: '6px 10px', borderRadius: '6px', outline: 'none', fontSize: '12px' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>SPEAKER TAG</label>
                  <input
                    type="text"
                    value={activeSeg.speaker || 'Speaker 1'}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'speaker', e.target.value)}
                    style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', color: '#fff', padding: '6px 10px', borderRadius: '6px', outline: 'none', fontSize: '12px' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>SPEED FACTOR</label>
                  <select
                    value={activeSeg.speed || 1.0}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'speed', parseFloat(e.target.value))}
                    style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', color: '#fff', padding: '6px 10px', borderRadius: '6px', outline: 'none', fontSize: '12px' }}
                  >
                    <option value={0.90}>0.90x (Slow & Natural)</option>
                    <option value={0.95}>0.95x (Standard Movie)</option>
                    <option value={1.00}>1.00x (Default Speed)</option>
                    <option value={1.05}>1.05x (Fast & Clean)</option>
                    <option value={1.10}>1.10x (Very Fast)</option>
                  </select>
                </div>
              </div>
            );
          })() : (
            <span style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic' }}>Select a segment to edit details</span>
          )}
        </div>
      </div>
    </div>
  );
};
