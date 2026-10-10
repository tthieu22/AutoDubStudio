import React, { useState } from 'react';
import { Film, Youtube, Smartphone, FileText, Download, Share2, Sparkles, CheckCircle2 } from 'lucide-react';
import { PythonEngineService } from '../services/pythonEngine';

interface ExportPresetsProps {
  projectDir: string;
}

export const ExportPresets: React.FC<ExportPresetsProps> = ({ projectDir }) => {
  const [selectedPreset, setSelectedPreset] = useState<'youtube' | 'tiktok' | 'audio_only' | 'srt'>('youtube');
  const [isExporting, setIsExporting] = useState(false);

  const presets = [
    {
      id: 'youtube',
      name: 'YouTube Standard (1080p HD)',
      icon: Youtube,
      color: '#ef4444',
      aspectRatio: '16:9 Landscape',
      res: '1920 x 1080 @ 60 FPS',
      desc: 'High-bitrate rendering optimized for YouTube and Desktop players. Embeds burn-in subtitles and sidechain audio ducking.'
    },
    {
      id: 'tiktok',
      name: 'TikTok & Shorts (9:16 Vertical)',
      icon: Smartphone,
      color: '#06b6d4',
      aspectRatio: '9:16 Portrait',
      res: '1080 x 1920 (Vertical Crop)',
      desc: 'Mobile-first layout crop designed for vertical displays like TikTok, Instagram Reels, and YouTube Shorts.'
    },
    {
      id: 'audio_only',
      name: 'Audio Dubbing Track Only (.WAV)',
      icon: Film,
      color: '#a855f7',
      aspectRatio: 'Stereo Audio Only',
      res: '320kbps High Quality WAV',
      desc: 'Extract only the synchronized Vietnamese dubbed master audio. Suitable for external DAW editors or podcast platforms.'
    },
    {
      id: 'srt',
      name: 'Standalone Subtitles (.SRT)',
      icon: FileText,
      color: '#10b981',
      aspectRatio: 'Text Subtitle File',
      res: 'UTF-8 Encoded SRT File',
      desc: 'Export independent Vietnamese translation text subtitles compatible with Adobe Premiere, CapCut, or DaVinci.'
    }
  ];

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await PythonEngineService.openOutputFolder(projectDir);
    } catch (err) {
      console.error(err);
    } finally {
      setIsExporting(false);
    }
  };

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
          <Share2 color="#06b6d4" size={18} />
          <div>
            <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#fff' }}>Export Presets & Publishing</h3>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Select rendering targets and open output delivery folder</span>
          </div>
        </div>

        <button className="btn-primary" onClick={handleExport} disabled={isExporting} style={{ padding: '6px 14px', fontSize: '12px' }}>
          <Download size={13} /> Open Output Folder
        </button>
      </div>

      {/* 2. PRESETS SELECTION */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', overflowY: 'auto', flexGrow: 1 }}>
        {presets.map(p => {
          const Icon = p.icon;
          const isSelected = selectedPreset === p.id;
          return (
            <div
              key={p.id}
              onClick={() => setSelectedPreset(p.id as any)}
              style={{
                padding: '16px',
                cursor: 'pointer',
                borderRadius: '10px',
                background: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.01)',
                border: '1px solid',
                borderColor: isSelected ? p.color : 'rgba(255, 255, 255, 0.05)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                transition: 'all 0.15s ease',
                height: 'fit-content'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Icon size={18} color={p.color} />
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>{p.name}</span>
                </div>
                {isSelected && <CheckCircle2 size={16} color="#10b981" />}
              </div>

              <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
                {p.desc}
              </p>

              <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                <span style={{ fontSize: '10px', color: '#64748b', background: 'rgba(255,255,255,0.03)', padding: '2px 6px', borderRadius: '4px' }}>
                  Ratio: {p.aspectRatio}
                </span>
                <span style={{ fontSize: '10px', color: '#64748b', background: 'rgba(255,255,255,0.03)', padding: '2px 6px', borderRadius: '4px' }}>
                  Res: {p.res}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
