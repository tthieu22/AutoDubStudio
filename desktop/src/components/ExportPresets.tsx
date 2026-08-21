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
      name: 'YouTube Standard (1080p Full HD)',
      icon: Youtube,
      color: '#ef4444',
      aspectRatio: '16:9',
      res: '1920 x 1080 @ 60 FPS',
      desc: 'Tối ưu chuẩn bitrate cao cho YouTube, Facebook Video. Tích hợp phụ đề Burn-in và âm thanh Sidechain Ducking.'
    },
    {
      id: 'tiktok',
      name: 'TikTok & Shorts (9:16 Vertical Video)',
      icon: Smartphone,
      color: '#06b6d4',
      aspectRatio: '9:16',
      res: '1080 x 1920 (Vertical Crop)',
      desc: 'Tự động cắt khung hình dọc phù hợp xem màn hình điện thoại di động TikTok, Instagram Reels, YouTube Shorts.'
    },
    {
      id: 'audio_only',
      name: 'Audio Dubbing Track Only (.MP3 / .WAV)',
      icon: Film,
      color: '#a855f7',
      aspectRatio: 'Audio Only',
      res: '320kbps High Quality Audio',
      desc: 'Xuất nguyên bản track âm thanh thuyết minh tiếng Việt đã trộn hoàn chỉnh để làm Podcast hoặc dùng cho hậu kỳ dựng phim.'
    },
    {
      id: 'srt',
      name: 'Standalone Subtitle (.SRT / .VTT)',
      icon: FileText,
      color: '#10b981',
      aspectRatio: 'Text Subtitle',
      res: 'UTF-8 Encoded SRT File',
      desc: 'Trích xuất file phụ đề tiếng Việt độc lập chuẩn ISO cho phép import vào Premiere Pro, CapCut, DaVinci Resolve.'
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
      {/* HEADER */}
      <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Share2 color="#06b6d4" size={22} />
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#fff' }}>EXPORT PRESETS & MULTI-PLATFORM PUBLISHING</h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Xuất bản video lồng tiếng theo định dạng tối ưu cho YouTube, TikTok, Shorts, Facebook</span>
          </div>
        </div>

        <button className="btn-primary" onClick={handleExport} disabled={isExporting}>
          <Download size={15} /> Mở Thư Mục Xuất (Open Output)
        </button>
      </div>

      {/* PRESETS GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
        {presets.map(p => {
          const Icon = p.icon;
          const isSelected = selectedPreset === p.id;
          return (
            <div
              key={p.id}
              onClick={() => setSelectedPreset(p.id as any)}
              className="glass-card"
              style={{
                padding: '20px',
                cursor: 'pointer',
                background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(15, 23, 42, 0.5)',
                border: isSelected ? `2px solid ${p.color}` : '1px solid var(--border-glass)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Icon size={22} color={p.color} />
                  <span style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>{p.name}</span>
                </div>
                {isSelected && <CheckCircle2 size={18} color="#10b981" />}
              </div>

              <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
                {p.desc}
              </p>

              <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                <span className="badge badge-completed" style={{ fontSize: '10px' }}>Ratio: {p.aspectRatio}</span>
                <span className="badge badge-pending" style={{ fontSize: '10px' }}>Res: {p.res}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
