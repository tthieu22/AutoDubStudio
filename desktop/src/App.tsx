import React, { useState } from 'react';

export default function App() {
  const [videoPath, setVideoPath] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <header style={{ borderBottom: '1px solid #334155', paddingBottom: '12px', marginBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', color: '#38bdf8' }}>AutoDubStudio MVP v0.1</h1>
        <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '13px' }}>100% Local AI Video Translation & Dubbing</p>
      </header>

      {/* Import Video Card */}
      <div style={{ background: '#1e293b', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
        <button 
          onClick={() => setVideoPath('d:/FullStack/AutoDubStudio/projects/my-video/source/input.mp4')}
          style={{ background: '#0284c7', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
        >
          Import Video
        </button>
        {videoPath ? (
          <div style={{ marginTop: '12px', color: '#cbd5e1' }}>
            <div><strong>File:</strong> input.mp4</div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>Duration: 00:35:21</div>
          </div>
        ) : (
          <div style={{ marginTop: '8px', color: '#64748b', fontSize: '13px' }}>No video imported yet</div>
        )}
      </div>

      {/* Settings Grid */}
      <div style={{ background: '#1e293b', padding: '16px', borderRadius: '8px', marginBottom: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>Source Language</label>
          <select style={{ width: '100%', background: '#0f172a', color: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #334155' }}>
            <option value="en">English</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>Target Language</label>
          <select style={{ width: '100%', background: '#0f172a', color: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #334155' }}>
            <option value="vi">Vietnamese</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>Whisper Model</label>
          <select style={{ width: '100%', background: '#0f172a', color: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #334155' }}>
            <option value="small">Small (int8)</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>Translation LLM</label>
          <select style={{ width: '100%', background: '#0f172a', color: '#fff', padding: '6px', borderRadius: '4px', border: '1px solid #334155' }}>
            <option value="qwen2.5:3b">Qwen 2.5 3B</option>
          </select>
        </div>
      </div>

      {/* Controls */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <button 
          onClick={() => setIsRunning(true)}
          style={{ background: '#16a34a', color: '#fff', border: 'none', padding: '8px 24px', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
        >
          Start Pipeline
        </button>
        <button 
          onClick={() => setIsRunning(false)}
          style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '8px 24px', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
        >
          Cancel
        </button>
      </div>

      {/* Pipeline Status Skeleton */}
      <div style={{ background: '#1e293b', padding: '16px', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#f8fafc' }}>Pipeline Progress</h3>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '14px', lineHeight: '2' }}>
          <li style={{ color: '#4ade80' }}>✓ Extract Audio</li>
          <li style={{ color: '#4ade80' }}>✓ Transcription</li>
          <li style={{ color: '#38bdf8' }}>● Translation (45%)</li>
          <li style={{ color: '#64748b' }}>○ TTS</li>
          <li style={{ color: '#64748b' }}>○ Sync</li>
          <li style={{ color: '#64748b' }}>○ Render</li>
        </ul>
        <div style={{ marginTop: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
            <span>Overall Progress</span>
            <span>72%</span>
          </div>
          <div style={{ width: '100%', background: '#0f172a', borderRadius: '4px', height: '10px', overflow: 'hidden' }}>
            <div style={{ width: '72%', background: '#38bdf8', height: '100%' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}
