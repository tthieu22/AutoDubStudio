import React, { useState, useEffect } from 'react';
import { CanvasLayer, LayerPreviewCanvas } from './LayerPreviewCanvas';
import { HistoryManager } from '../services/historyManager';
import { PythonEngineService } from '../services/pythonEngine';

interface TimelineEditorProps {
  projectDir: string;
}

export const TimelineEditor: React.FC<TimelineEditorProps> = ({ projectDir }) => {
  const [composition, setComposition] = useState<{
    width: number;
    height: number;
    fps: number;
    duration: number;
    layers: CanvasLayer[];
  }>({
    width: 1920,
    height: 1080,
    fps: 30,
    duration: 120,
    layers: []
  });

  const [selectedLayerId, setSelectedLayerId] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [history] = useState(() => new HistoryManager<any>());

  useEffect(() => {
    loadComposition();
  }, [projectDir]);

  const loadComposition = async () => {
    try {
      const data = await PythonEngineService.readComposition(projectDir);
      if (data && data.layers) {
        setComposition(data);
        history.clear();
        history.push(data);
        if (data.layers.length > 0) {
          setSelectedLayerId(data.layers[0].id);
        }
      }
    } catch (e) {
      console.error("Failed to load composition:", e);
    }
  };

  const updateCompositionState = (newComp: typeof composition, pushHistory = true) => {
    setComposition(newComp);
    if (pushHistory) {
      history.push(newComp);
    }
    PythonEngineService.writeComposition(projectDir, newComp);
  };

  const handleUndo = () => {
    const prev = history.undo(composition);
    if (prev) {
      setComposition(prev);
      PythonEngineService.writeComposition(projectDir, prev);
    }
  };

  const handleRedo = () => {
    const next = history.redo(composition);
    if (next) {
      setComposition(next);
      PythonEngineService.writeComposition(projectDir, next);
    }
  };

  const handleAddLayer = (type: 'title' | 'text' | 'logo' | 'image') => {
    const id = `layer-${type}-${Date.now().toString().slice(-4)}`;
    const newLayer: CanvasLayer = {
      id,
      type,
      text: type === 'logo' ? 'WATERMARK LOGO' : 'NEW TEXT LAYER',
      start: 0,
      duration: type === 'logo' ? 120 : 10,
      x: type === 'logo' ? 1600 : 800,
      y: type === 'logo' ? 80 : 500,
      scale: 1.0,
      opacity: 1.0,
      rotation: 0,
      z_index: composition.layers.length + 1,
      style: { font_size: type === 'title' ? 48 : 32, color: type === 'logo' ? '#38bdf8' : '#ffffff', border_width: 2, border_color: '#000000' },
      visible: true,
      locked: false
    };

    const updated = { ...composition, layers: [...composition.layers, newLayer] };
    updateCompositionState(updated);
    setSelectedLayerId(id);
  };

  const handleUpdateLayer = (updatedLayer: CanvasLayer) => {
    const updatedLayers = composition.layers.map(l => l.id === updatedLayer.id ? updatedLayer : l);
    updateCompositionState({ ...composition, layers: updatedLayers });
  };

  const handleDeleteLayer = (id: string) => {
    const updatedLayers = composition.layers.filter(l => l.id !== id);
    updateCompositionState({ ...composition, layers: updatedLayers });
    if (selectedLayerId === id) {
      setSelectedLayerId(updatedLayers.length > 0 ? updatedLayers[0].id : null);
    }
  };

  const selectedLayer = composition.layers.find(l => l.id === selectedLayerId);

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 p-6 overflow-y-auto space-y-6">
      {/* Top Controls Toolbar */}
      <div className="flex items-center justify-between bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-600/20 text-indigo-400 p-2 rounded-lg border border-indigo-500/30">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h18M3 16h18" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-wide">Multi-Track Video Timeline & Layer Studio</h2>
            <p className="text-xs text-slate-400">Interactive Layer Composition & Timeline Editor</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleUndo}
            disabled={!history.canUndo()}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs font-semibold rounded-lg border border-slate-700 transition"
          >
            ↩ Undo (Ctrl+Z)
          </button>
          <button
            onClick={handleRedo}
            disabled={!history.canRedo()}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs font-semibold rounded-lg border border-slate-700 transition"
          >
            ↪ Redo (Ctrl+Y)
          </button>
          <div className="h-6 w-px bg-slate-800 mx-2" />
          <button
            onClick={() => handleAddLayer('title')}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white rounded-lg shadow-lg shadow-indigo-600/30 transition"
          >
            + Add Title
          </button>
          <button
            onClick={() => handleAddLayer('text')}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 rounded-lg border border-slate-700 transition"
          >
            + Add Text
          </button>
          <button
            onClick={() => handleAddLayer('logo')}
            className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-xs font-bold text-white rounded-lg shadow-lg shadow-cyan-600/30 transition"
          >
            + Add Logo Watermark
          </button>
        </div>
      </div>

      {/* Main Split View: Left Canvas Preview, Right Layer Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <LayerPreviewCanvas
            layers={composition.layers}
            selectedLayerId={selectedLayerId}
            onSelectLayer={setSelectedLayerId}
            onUpdateLayer={handleUpdateLayer}
            currentTime={currentTime}
          />

          {/* Timeline Playback Scrubber */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 shadow-md">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-lg border border-slate-700 transition"
              >
                {isPlaying ? '⏸ Pause' : '▶ Play'}
              </button>
              <div>
                Time: <span className="text-indigo-400 font-bold">{currentTime.toFixed(2)}s</span> / {composition.duration.toFixed(2)}s
              </div>
            </div>
            <input
              type="range"
              min={0}
              max={composition.duration}
              step={0.1}
              value={currentTime}
              onChange={e => setCurrentTime(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>
        </div>

        {/* Right Layer Inspector */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5 shadow-xl">
          <h3 className="text-sm font-bold tracking-wider text-slate-300 uppercase border-b border-slate-800 pb-2">
            Layer Properties & Inspector
          </h3>

          {selectedLayer ? (
            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Layer Label / Content</label>
                <input
                  type="text"
                  value={selectedLayer.text || ''}
                  onChange={e => handleUpdateLayer({ ...selectedLayer, text: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Position X (px)</label>
                  <input
                    type="number"
                    value={selectedLayer.x}
                    onChange={e => handleUpdateLayer({ ...selectedLayer, x: parseInt(e.target.value) || 0 })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Position Y (px)</label>
                  <input
                    type="number"
                    value={selectedLayer.y}
                    onChange={e => handleUpdateLayer({ ...selectedLayer, y: parseInt(e.target.value) || 0 })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Font Size (pt)</label>
                  <input
                    type="number"
                    value={selectedLayer.style?.font_size || 36}
                    onChange={e => handleUpdateLayer({ ...selectedLayer, style: { ...selectedLayer.style, font_size: parseInt(e.target.value) || 24 } })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Color</label>
                  <input
                    type="color"
                    value={selectedLayer.style?.color || '#ffffff'}
                    onChange={e => handleUpdateLayer({ ...selectedLayer, style: { ...selectedLayer.style, color: e.target.value } })}
                    className="w-full h-9 bg-slate-950 border border-slate-800 rounded-lg p-1 cursor-pointer"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Opacity ({Math.round(selectedLayer.opacity * 100)}%)</label>
                <input
                  type="range"
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  value={selectedLayer.opacity}
                  onChange={e => handleUpdateLayer({ ...selectedLayer, opacity: parseFloat(e.target.value) })}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Fade In (sec)</label>
                  <input
                    type="number"
                    min={0}
                    max={5}
                    step={0.1}
                    value={selectedLayer.fade_in_sec || 0}
                    onChange={e => handleUpdateLayer({ ...selectedLayer, fade_in_sec: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Fade Out (sec)</label>
                  <input
                    type="number"
                    min={0}
                    max={5}
                    step={0.1}
                    value={selectedLayer.fade_out_sec || 0}
                    onChange={e => handleUpdateLayer({ ...selectedLayer, fade_out_sec: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-between items-center">
                <button
                  onClick={() => handleUpdateLayer({ ...selectedLayer, visible: !selectedLayer.visible })}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition ${
                    selectedLayer.visible
                      ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-400'
                      : 'bg-slate-800 border-slate-700 text-slate-400'
                  }`}
                >
                  {selectedLayer.visible ? '👁 Visible' : '🙈 Hidden'}
                </button>
                <button
                  onClick={() => handleDeleteLayer(selectedLayer.id)}
                  className="px-3 py-1.5 bg-rose-950/40 hover:bg-rose-900/60 text-rose-400 font-semibold rounded-lg border border-rose-800/60 transition"
                >
                  🗑 Delete Layer
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-slate-500 text-xs">
              Select a layer on the preview canvas or timeline to view properties.
            </div>
          )}
        </div>
      </div>

      {/* Multi-Track Timeline Overview Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold tracking-wider text-slate-300 uppercase border-b border-slate-800 pb-2">
          Multi-Track Layer Stacking
        </h3>

        <div className="space-y-2">
          {composition.layers.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-xs font-mono">
              No custom layers added yet. Click "+ Add Title" or "+ Add Logo Watermark" above to get started.
            </div>
          ) : (
            composition.layers.map((layer, idx) => (
              <div
                key={layer.id}
                onClick={() => setSelectedLayerId(layer.id)}
                className={`flex items-center justify-between px-4 py-3 rounded-lg border transition cursor-pointer ${
                  selectedLayerId === layer.id
                    ? 'bg-indigo-950/40 border-indigo-500/80 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800/80 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-xs font-mono px-2 py-0.5 bg-slate-800 text-slate-300 rounded">
                    Track #{idx + 1}
                  </span>
                  <span className="font-bold text-xs capitalize text-slate-200">[{layer.type}]</span>
                  <span className="text-xs font-medium text-slate-300 truncate max-w-xs">{layer.text || layer.source}</span>
                </div>
                <div className="flex items-center space-x-4 text-xs font-mono text-slate-500">
                  <span>Start: {layer.start}s</span>
                  <span>Duration: {layer.duration === 0 ? 'Full' : `${layer.duration}s`}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
