import React, { useState, useRef } from 'react';
import { Mic, Volume2, Play, Square, Loader2, Sparkles, Sliders, CheckCircle2, VolumeX, User } from 'lucide-react';
import { PythonEngineService } from '../services/pythonEngine';

import { StageName, StageProgressInfo, PipelineStatus } from '../types/pipeline';

interface VoiceStudioProps {
  projectDir: string;
  pipelineStatus: PipelineStatus;
  stageProgresses: Partial<Record<StageName, StageProgressInfo>>;
  onResumePipeline: (stopAt?: string) => Promise<void>;
}

export const VoiceStudio: React.FC<VoiceStudioProps> = ({ 
  projectDir, 
  pipelineStatus, 
  stageProgresses, 
  onResumePipeline 
}) => {
  const [speakers, setSpeakers] = useState([
    { id: 'Speaker 1', gender: 'Female', voice: 'edge-tts-vi-hoaimy', speed: 0.95, pitch: 'Normal' },
    { id: 'Speaker 2', gender: 'Male', voice: 'edge-tts-vi-namminh', speed: 0.95, pitch: 'Deep' }
  ]);

  const [previewText, setPreviewText] = useState('Bộ phim bắt đầu khi anh chàng chính của chúng ta vô tình phát hiện ra một bí mật bị ẩn giấu suốt 20 năm qua...');
  const [selectedSpeaker, setSelectedSpeaker] = useState('Speaker 1');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const voiceBank = [
    { id: 'edge-tts-vi-hoaimy', name: '🎬 Female Review (Hoài My Neural)', gender: 'Female', region: 'North' },
    { id: 'edge-tts-vi-namminh', name: '🎬 Male Storytelling (Nam Minh Neural)', gender: 'Male', region: 'North' },
    { id: 'vi_VN-vais1000-medium', name: '🎙️ Female Cinematic (Vais 1000 Premium)', gender: 'Female', region: 'North' },
    { id: 'vi_VN-vnu-medium', name: '🎙️ Male Documentary (VNU Deep Voice)', gender: 'Male', region: 'North' },
    { id: 'vi_VN-southern-female', name: '🎙️ Southern Female (Sài Gòn Soft Voice)', gender: 'Female', region: 'South' }
  ];

  const handleSpeakerVoiceChange = (speakerId: string, voiceId: string) => {
    setSpeakers(prev => prev.map(s => s.id === speakerId ? { ...s, voice: voiceId } : s));
  };

  const handleStopAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
    setIsGenerating(false);
  };

  const handleGeneratePreview = async () => {
    if (isPlaying) {
      handleStopAudio();
      return;
    }

    setIsGenerating(true);
    handleStopAudio();

    const activeSpk = speakers.find(s => s.id === selectedSpeaker) || speakers[0];
    const targetSpeed = activeSpk?.speed || 1.0;
    const cleanText = previewText.trim() || 'Bộ phim bắt đầu khi anh chàng chính vô tình phát hiện bí mật...';

    try {
      // 1. Call Python Engine to synthesize authentic Neural voice
      const res = await PythonEngineService.previewTtsVoice(cleanText, activeSpk.voice, activeSpk.gender);

      if (res && res.audio_b64) {
        const audio = new Audio(res.audio_b64);
        currentAudioRef.current = audio;
        audio.playbackRate = targetSpeed;

        audio.onplay = () => {
          setIsGenerating(false);
          setIsPlaying(true);
        };

        audio.onended = () => {
          setIsPlaying(false);
          currentAudioRef.current = null;
        };

        audio.onerror = () => {
          fallbackGoogleTTS(cleanText, targetSpeed);
        };

        await audio.play();
        return;
      }
    } catch (err) {
      console.warn('Python TTS preview error, falling back to Google stream:', err);
    }

    // 2. Fallback to Google Stream
    fallbackGoogleTTS(cleanText, targetSpeed);
  };

  const fallbackGoogleTTS = (text: string, speed: number) => {
    const ttsUrl = `https://translate.google.com/translate_tts?ie=UTF-8&tl=vi&client=tw-ob&q=${encodeURIComponent(text)}`;
    try {
      const audio = new Audio(ttsUrl);
      currentAudioRef.current = audio;
      audio.playbackRate = speed;
      audio.onplay = () => {
        setIsGenerating(false);
        setIsPlaying(true);
      };
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => setIsPlaying(false);
      audio.play().catch(() => setIsPlaying(false));
    } catch (e) {
      setIsGenerating(false);
      setIsPlaying(false);
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
          <Mic color="#6366f1" size={18} />
          <div>
            <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#fff' }}>Voice Studio & Casting Console</h3>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Assign voice models, customize speech speed, and preview characters offline</span>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {pipelineStatus === 'RUNNING' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: '#94a3b8' }}>
              <Loader2 size={12} className="animate-spin" color="#06b6d4" />
              <span>
                {stageProgresses['TTS']?.status === 'RUNNING' && `TTS Progress: ${stageProgresses['TTS']?.progress}%`}
                {stageProgresses['SYNC']?.status === 'RUNNING' && `Syncing audio timeline...`}
              </span>
            </div>
          )}
          
          <button 
            className="btn-primary" 
            onClick={() => onResumePipeline('sync')}
            disabled={pipelineStatus === 'RUNNING'}
            style={{ padding: '6px 14px', fontSize: '12px', background: 'linear-gradient(135deg, #a855f7, #6366f1)' }}
          >
            {pipelineStatus === 'RUNNING' ? 'Running Generation...' : 'Generate Voice & Time-Sync ➔'}
          </button>
        </div>
      </div>

      {/* 2. DUAL PANEL LAYOUT */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '16px', flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* SPEAKERS MANAGEMENT */}
        <div 
          style={{ 
            background: '#111318', 
            border: '1px solid rgba(255, 255, 255, 0.05)', 
            borderRadius: '10px', 
            padding: '16px', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '12px',
            overflowY: 'auto' 
          }}
        >
          <span style={{ fontSize: '10px', fontWeight: 800, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Cast Members
          </span>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            {speakers.map(spk => {
              const isSelected = selectedSpeaker === spk.id;
              const activeVoice = voiceBank.find(v => v.id === spk.voice);
              return (
                <div
                  key={spk.id}
                  onClick={() => setSelectedSpeaker(spk.id)}
                  style={{
                    padding: '14px',
                    background: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.01)',
                    border: '1px solid',
                    borderColor: isSelected ? '#6366f1' : 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#0B0D10', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <User size={14} style={{ color: isSelected ? '#6366f1' : '#64748b' }} />
                      </div>
                      <span style={{ fontWeight: 700, color: '#fff', fontSize: '13px' }}>{spk.id}</span>
                    </div>
                    <span style={{ fontSize: '9px', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px', color: '#94a3b8' }}>
                      {spk.gender}
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span style={{ fontSize: '10px', color: '#64748b' }}>VOICE CHARACTER</span>
                      <select
                        value={spk.voice}
                        onChange={(e) => handleSpeakerVoiceChange(spk.id, e.target.value)}
                        style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', color: '#fff', padding: '6px', borderRadius: '4px', fontSize: '11px', outline: 'none', marginTop: '3px' }}
                      >
                        {voiceBank.map(v => (
                          <option key={v.id} value={v.id}>{v.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <span style={{ fontSize: '10px', color: '#64748b' }}>SPEED COEFFICIENT</span>
                      <select
                        value={spk.speed}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value);
                          setSpeakers(prev => prev.map(s => s.id === spk.id ? { ...s, speed: val } : s));
                        }}
                        style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', color: '#fff', padding: '6px', borderRadius: '4px', fontSize: '11px', outline: 'none', marginTop: '3px' }}
                      >
                        <option value={0.90}>0.90x (Relaxed)</option>
                        <option value={0.95}>0.95x (Natural)</option>
                        <option value={1.00}>1.00x (Standard)</option>
                        <option value={1.05}>1.05x (Fast)</option>
                      </select>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* AUDITION ROOM */}
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
              Audition Room
            </span>
            <h4 style={{ margin: '4px 0 0 0', fontSize: '14px', fontWeight: 700, color: '#fff' }}>
              Testing Speaker: <span style={{ color: '#6366f1' }}>{selectedSpeaker}</span>
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1 }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Preview Text Script</span>
            <textarea
              value={previewText}
              onChange={(e) => setPreviewText(e.target.value)}
              rows={5}
              style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '12px', outline: 'none', resize: 'none' }}
            />

            {/* Playback animation wave */}
            {isPlaying && (
              <div style={{ padding: '12px', background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.15)', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ display: 'flex', gap: '2px', alignItems: 'center' }}>
                  <div className="wave-bar" style={{ width: '3px', height: '14px', background: '#06b6d4', borderRadius: '1px', animation: 'bounce 0.5s ease infinite alternate' }} />
                  <div className="wave-bar" style={{ width: '3px', height: '22px', background: '#06b6d4', borderRadius: '1px', animation: 'bounce 0.5s ease infinite alternate 0.1s' }} />
                  <div className="wave-bar" style={{ width: '3px', height: '10px', background: '#06b6d4', borderRadius: '1px', animation: 'bounce 0.5s ease infinite alternate 0.2s' }} />
                </div>
                <span style={{ fontSize: '11px', color: '#06b6d4', fontWeight: 600 }}>Synthesized audio stream playing...</span>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              className="btn-primary"
              onClick={handleGeneratePreview}
              disabled={isGenerating}
              style={{
                width: '100%',
                justifyContent: 'center',
                background: isPlaying ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' : undefined,
                padding: '10px',
                fontSize: '12px'
              }}
            >
              {isGenerating ? (
                <Loader2 size={14} className="animate-spin" />
              ) : isPlaying ? (
                <Square size={14} />
              ) : (
                <Play size={14} />
              )}
              {isGenerating
                ? 'Synthesizing Audio...'
                : isPlaying
                ? 'Stop Playback'
                : 'Audition Voice Model'}
            </button>

            <div style={{ display: 'flex', gap: '6px', alignItems: 'center', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', padding: '10px' }}>
              <CheckCircle2 size={14} color="#10b981" style={{ flexShrink: 0 }} />
              <span style={{ fontSize: '11px', color: '#94a3b8', lineHeight: 1.3 }}>
                Multi-speaker pace ducking is pre-configured on sync stages.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
