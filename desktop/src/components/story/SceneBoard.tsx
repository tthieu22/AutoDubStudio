import React, { useState } from 'react';
import { 
  Clapperboard, 
  Grid, 
  List, 
  Plus, 
  Copy, 
  Trash2, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  MapPin, 
  Sparkles,
  Eye,
  Sliders,
  Image as ImageIcon
} from 'lucide-react';

import { PythonEngineService } from '../../services/pythonEngine';

export interface SceneItem {
  id: string;
  sceneNumber: number;
  location: string;
  timeOfDay: string;
  emotion: string;
  duration: number;
  narration: string;
  dialogue: string;
  status: 'GENERATED' | 'REVIEW_REQUIRED' | 'APPROVED' | 'REJECTED';
  imageUrl?: string;
}

interface SceneBoardProps {
  projectDir?: string | null;
  onSelectScene?: (scene: SceneItem) => void;
}

export const SceneBoard: React.FC<SceneBoardProps> = ({ projectDir, onSelectScene }) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'storyboard'>('storyboard');
  const [scenes, setScenes] = useState<SceneItem[]>([]);

  React.useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (data && data.scenes && Array.isArray(data.scenes)) {
          setScenes(data.scenes);
        }
      }).catch(console.error);
    }
  }, [projectDir]);

  const [selectedSceneId, setSelectedSceneId] = useState<string>('');

  const saveScenesToProject = async (newScenes: SceneItem[]) => {
    setScenes(newScenes);
    if (projectDir) {
      try {
        const json = (await PythonEngineService.readProjectJson(projectDir)) || {};
        json.scenes = newScenes;
        await PythonEngineService.writeProjectJson(projectDir, json);
      } catch (e) {
        console.error('Failed to save scenes to project.json:', e);
      }
    }
  };

  const updateStatus = (id: string, newStatus: SceneItem['status']) => {
    const updated = scenes.map(s => s.id === id ? { ...s, status: newStatus } : s);
    saveScenesToProject(updated);
  };

  const duplicateScene = (id: string) => {
    const original = scenes.find(s => s.id === id);
    if (!original) return;
    const dup: SceneItem = {
      ...original,
      id: `scene-${Date.now()}`,
      sceneNumber: scenes.length + 1,
      status: 'GENERATED'
    };
    saveScenesToProject([...scenes, dup]);
  };

  const deleteScene = (id: string) => {
    const updated = scenes.filter(s => s.id !== id);
    saveScenesToProject(updated);
  };

  const getStatusBadge = (st: SceneItem['status']) => {
    switch (st) {
      case 'APPROVED':
        return <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold">✓ APPROVED</span>;
      case 'REVIEW_REQUIRED':
        return <span className="px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[10px] font-bold">! REVIEW REQUIRED</span>;
      case 'REJECTED':
        return <span className="px-2 py-0.5 rounded bg-rose-500/15 border border-rose-500/30 text-rose-300 text-[10px] font-bold">× REJECTED</span>;
      case 'GENERATED':
      default:
        return <span className="px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-[10px] font-bold">● GENERATED</span>;
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* TOOLBAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <Clapperboard size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Scene Board & Storyboard
            </h2>
            <p className="text-xs text-slate-400">
              Organize narrative scenes, visual prompts, dialogue timings, and scene approval gates.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* VIEW SWITCHER */}
          <div className="flex items-center bg-black/40 p-0.5 rounded-lg border border-white/5">
            <button
              onClick={() => setViewMode('storyboard')}
              className={`p-1.5 rounded-md text-xs font-semibold flex items-center gap-1 transition-all ${
                viewMode === 'storyboard' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
              title="Storyboard View"
            >
              <Clapperboard size={14} /> Storyboard
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-md text-xs font-semibold flex items-center gap-1 transition-all ${
                viewMode === 'grid' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
              title="Grid View"
            >
              <Grid size={14} /> Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-md text-xs font-semibold flex items-center gap-1 transition-all ${
                viewMode === 'list' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
              title="List View"
            >
              <List size={14} /> List
            </button>
          </div>

          <button
            onClick={() => {
              const newScene: SceneItem = {
                id: `scene-${Date.now()}`,
                sceneNumber: scenes.length + 1,
                location: 'New Location',
                timeOfDay: 'Day',
                emotion: 'Neutral',
                duration: 5.0,
                narration: 'Narration text...',
                dialogue: 'Character dialogue...',
                status: 'GENERATED'
              };
              saveScenesToProject([...scenes, newScene]);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all"
          >
            <Plus size={14} /> Add Scene
          </button>
        </div>
      </div>

      {/* SCENE CARDS CONTAINER */}
      <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar">
        {scenes.length === 0 ? (
          <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 mb-4 shadow-lg shadow-cyan-500/10">
              <Clapperboard size={28} />
            </div>
            <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Dự Án Chưa Có Phân Cảnh Video</h3>
            <p className="text-xs text-slate-400 max-w-md mb-5 leading-relaxed">
              Các phân cảnh video (Scene Board & Storyboard) sẽ được tự động tạo từ Kịch Bản Truyện khi bạn tiến hành xử lý dự án.
            </p>
            <button
              onClick={() => {
                const newScene: SceneItem = {
                  id: `scene-${Date.now()}`,
                  sceneNumber: 1,
                  location: 'Bối cảnh phân cảnh 1',
                  timeOfDay: 'Ban ngày',
                  emotion: 'Hào hứng',
                  duration: 5.0,
                  narration: 'Nội dung lời dẫn chuyện...',
                  dialogue: 'Lời thoại nhân vật...',
                  status: 'GENERATED'
                };
                saveScenesToProject([...scenes, newScene]);
              }}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-indigo-600/20 transition-all cursor-pointer"
            >
              <Plus size={16} /> Thêm Phân Cảnh Mới
            </button>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-3'}>
            {scenes.map(scene => {
            const isSelected = selectedSceneId === scene.id;
            return (
              <div
                key={scene.id}
                onClick={() => {
                  setSelectedSceneId(scene.id);
                  onSelectScene?.(scene);
                }}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-indigo-500/10 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                    : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
                }`}
              >
                {/* CARD HEADER */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-md bg-indigo-600/20 text-indigo-300 font-bold text-xs flex items-center justify-center border border-indigo-500/30">
                      #{scene.sceneNumber}
                    </span>
                    <span className="text-xs font-bold text-white font-['Outfit']">{scene.location}</span>
                    <span className="text-[11px] text-slate-500">• {scene.timeOfDay}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusBadge(scene.status)}
                    <span className="text-xs font-mono text-cyan-400 font-semibold flex items-center gap-1">
                      <Clock size={12} /> {scene.duration}s
                    </span>
                  </div>
                </div>

                {/* VISUAL IMAGE PLACEHOLDER */}
                <div className="w-full h-32 bg-black/40 rounded-lg border border-white/5 my-2 flex flex-col items-center justify-center text-slate-500 relative overflow-hidden group">
                  <ImageIcon size={28} className="mb-1 text-slate-600" />
                  <span className="text-[11px]">AI Scene Image Preview</span>

                  {/* HOVER QUICK ACTIONS */}
                  <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 transition-all">
                    <button
                      onClick={(e) => { e.stopPropagation(); updateStatus(scene.id, 'APPROVED'); }}
                      className="px-2.5 py-1 rounded bg-emerald-500 text-black font-bold text-xs flex items-center gap-1"
                    >
                      <CheckCircle2 size={12} /> Approve
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); updateStatus(scene.id, 'REJECTED'); }}
                      className="px-2.5 py-1 rounded bg-rose-500 text-white font-bold text-xs flex items-center gap-1"
                    >
                      <XCircle size={12} /> Reject
                    </button>
                  </div>
                </div>

                {/* TEXT NARRATION & DIALOGUE */}
                <div className="space-y-1.5 text-xs text-slate-300 pt-2 border-t border-white/5">
                  <p><strong className="text-slate-500">Narration:</strong> {scene.narration}</p>
                  <p><strong className="text-indigo-400">Dialogue:</strong> {scene.dialogue}</p>
                </div>

                {/* CARD FOOTER ACTIONS */}
                <div className="flex items-center justify-between pt-3 mt-2 border-t border-white/5 text-xs text-slate-400">
                  <span className="text-[11px] text-slate-500 font-mono">Emotion: {scene.emotion}</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={(e) => { e.stopPropagation(); duplicateScene(scene.id); }}
                      className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white"
                      title="Duplicate Scene"
                    >
                      <Copy size={13} />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteScene(scene.id); }}
                      className="p-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400"
                      title="Delete Scene"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        )}
      </div>
    </div>
  );
};
