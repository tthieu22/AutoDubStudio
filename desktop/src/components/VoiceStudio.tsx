import React, { useState, useRef } from 'react';
import { Mic, Volume2, Play, Square, Loader2, Sparkles, Sliders, CheckCircle2, Volume2 as VolumeIcon } from 'lucide-react';
import { PythonEngineService } from '../services/pythonEngine';

interface VoiceStudioProps {
  projectDir: string;
}

export const VoiceStudio: React.FC<VoiceStudioProps> = ({ projectDir }) => {
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
    { id: 'edge-tts-vi-hoaimy', name: '🎬 Giọng Nữ Review Phim (Hoài My Neural - Truyền Cảm)', gender: 'Female', region: 'North' },
    { id: 'edge-tts-vi-namminh', name: '🎬 Giọng Nam Review Phim (Nam Minh Neural - Trầm Ấm Kể Chuyện)', gender: 'Male', region: 'North' },
    { id: 'vi_VN-vais1000-medium', name: '🎙️ Nữ Thuyết Minh Điện Ảnh (Vais 1000 Premium)', gender: 'Female', region: 'North' },
    { id: 'vi_VN-vnu-medium', name: '🎙️ Nam Thuyết Minh Tài Liệu (VNU Deep Voice)', gender: 'Male', region: 'North' },
    { id: 'vi_VN-southern-female', name: '🎙️ Nữ Miền Nam (Sài Gòn Soft Voice)', gender: 'Female', region: 'South' }
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

  const fallbackWebSpeech = (text: string, speed: number, gender?: string) => {
    setIsGenerating(false);
    setIsPlaying(true);

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'vi-VN';
      utterance.rate = speed;
      utterance.pitch = gender === 'Female' ? 1.1 : 0.85;

      // Find Vietnamese voice if available in system
      const voices = window.speechSynthesis.getVoices();
      const viVoice = voices.find(v => v.lang.includes('vi') || v.name.toLowerCase().includes('vietnam'));
      if (viVoice) {
        utterance.voice = viVoice;
      }

      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => setIsPlaying(false), 2500);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
      {/* HEADER */}
      <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Mic color="#a855f7" size={22} />
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#fff' }}>VOICE STUDIO & MULTI-SPEAKER ENGINE</h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Phân chia giọng đọc riêng biệt cho từng nhân vật, thử nghiệm nghe thử trực tiếp chuẩn tiếng Việt</span>
          </div>
        </div>

        <span className="badge badge-completed">PIPER ONNX CUDA + NEURAL TTS</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '20px', flexGrow: 1 }}>
        {/* SPEAKER MANAGEMENT TABLE */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h4 style={{ margin: 0, fontSize: '15px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={16} color="#a855f7" /> DANH SÁCH NHÂN VẬT & GIỌNG ĐỌC CẤU HÌNH
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {speakers.map(spk => {
              const isSelected = selectedSpeaker === spk.id;
              return (
                <div
                  key={spk.id}
                  onClick={() => setSelectedSpeaker(spk.id)}
                  style={{
                    padding: '16px',
                    background: isSelected ? 'rgba(168, 85, 247, 0.12)' : 'rgba(15, 23, 42, 0.6)',
                    border: isSelected ? '1px solid #a855f7' : '1px solid var(--border-glass)',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: '#fff', fontSize: '14px' }}>{spk.id} ({spk.gender})</span>
                    <span className="badge badge-pending">Piper Neural</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px', gap: '12px' }}>
                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>MÔ HÌNH GIỌNG ĐỌC (VOICE MODEL)</label>
                      <select
                        value={spk.voice}
                        onChange={(e) => handleSpeakerVoiceChange(spk.id, e.target.value)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid var(--border-glass)', color: '#fff', padding: '8px', borderRadius: '6px' }}
                      >
                        {voiceBank.map(v => (
                          <option key={v.id} value={v.id}>{v.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>TỐC ĐỘ (SPEED)</label>
                      <select
                        value={spk.speed}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value);
                          setSpeakers(prev => prev.map(s => s.id === spk.id ? { ...s, speed: val } : s));
                        }}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid var(--border-glass)', color: '#fff', padding: '8px', borderRadius: '6px' }}
                      >
                        <option value={0.90}>0.90x</option>
                        <option value={0.95}>0.95x</option>
                        <option value={1.00}>1.00x</option>
                        <option value={1.05}>1.05x</option>
                      </select>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* INSTANT SINGLE SEGMENT AUDITION PREVIEW */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h4 style={{ margin: 0, fontSize: '15px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Volume2 size={16} color="#38bdf8" /> GENERATE AUDITION PREVIEW
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <label style={{ fontSize: '11px', color: '#94a3b8' }}>DÙNG GIỌNG CỦA: <strong style={{ color: '#a855f7' }}>{selectedSpeaker}</strong></label>
            <textarea
              value={previewText}
              onChange={(e) => setPreviewText(e.target.value)}
              rows={4}
              style={{ width: '100%', background: '#0f172a', border: '1px solid var(--border-glass)', color: '#fff', padding: '10px', borderRadius: '8px', fontSize: '13px' }}
            />
          </div>

          <button
            className="btn-primary"
            onClick={handleGeneratePreview}
            disabled={isGenerating}
            style={{
              width: '100%',
              justifyContent: 'center',
              background: isPlaying ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' : undefined
            }}
          >
            {isGenerating ? (
              <Loader2 size={16} className="animate-spin" />
            ) : isPlaying ? (
              <Square size={16} />
            ) : (
              <Play size={16} />
            )}
            {isGenerating
              ? 'Đang tải luồng audio thuyết minh tiếng Việt...'
              : isPlaying
              ? '⏹ ĐANG PHÁT AUDIO (Dừng Nghe)'
              : '▶ CHẠY NGHE THỬ MẪU (Generate Preview)'}
          </button>

          {/* AUDIO ANIMATION WAVE INDICATOR */}
          {isPlaying && (
            <div style={{ padding: '12px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <VolumeIcon size={20} className="animate-bounce" color="#38bdf8" />
              <span style={{ fontSize: '12px', color: '#38bdf8', fontWeight: 700 }}>Đang phát loa audio thuyết minh tiếng Việt chuẩn...</span>
            </div>
          )}

          <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={16} color="#10b981" />
            <span style={{ fontSize: '12px', color: '#6ee7b7' }}>Giọng thuyết minh được tối ưu tốc độ ngắt nghỉ tự nhiên theo chuẩn IMDb documentary.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
