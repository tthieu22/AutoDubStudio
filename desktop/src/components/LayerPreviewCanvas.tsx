import React, { useState, useRef } from 'react';

export interface CanvasLayer {
  id: string;
  type: string;
  text?: string;
  source?: string;
  start: number;
  duration: number;
  x: number;
  y: number;
  width?: number;
  height?: number;
  scale: number;
  opacity: number;
  rotation: number;
  z_index: number;
  style: Record<string, any>;
  fade_in_sec?: number;
  fade_out_sec?: number;
  visible: boolean;
  locked: boolean;
}

interface LayerPreviewCanvasProps {
  layers: CanvasLayer[];
  selectedLayerId: string | null;
  onSelectLayer: (id: string) => void;
  onUpdateLayer: (updated: CanvasLayer) => void;
  currentTime: number;
  canvasWidth?: number;
  canvasHeight?: number;
}

export const LayerPreviewCanvas: React.FC<LayerPreviewCanvasProps> = ({
  layers,
  selectedLayerId,
  onSelectLayer,
  onUpdateLayer,
  currentTime,
  canvasWidth = 1920,
  canvasHeight = 1080
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const activeLayers = layers
    .filter(l => l.visible && (l.duration === 0 || (currentTime >= l.start && currentTime <= l.start + l.duration)))
    .sort((a, b) => a.z_index - b.z_index);

  const handleMouseDown = (e: React.MouseEvent, layer: CanvasLayer) => {
    if (layer.locked) return;
    e.stopPropagation();
    onSelectLayer(layer.id);
    setDraggingId(layer.id);

    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const scaleX = canvasWidth / rect.width;
      const scaleY = canvasHeight / rect.height;
      const clickX = (e.clientX - rect.left) * scaleX;
      const clickY = (e.clientY - rect.top) * scaleY;
      setDragOffset({ x: clickX - layer.x, y: clickY - layer.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggingId || !containerRef.current) return;
    const targetLayer = layers.find(l => l.id === draggingId);
    if (!targetLayer || targetLayer.locked) return;

    const rect = containerRef.current.getBoundingClientRect();
    const scaleX = canvasWidth / rect.width;
    const scaleY = canvasHeight / rect.height;
    const newX = Math.round((e.clientX - rect.left) * scaleX - dragOffset.x);
    const newY = Math.round((e.clientY - rect.top) * scaleY - dragOffset.y);

    onUpdateLayer({ ...targetLayer, x: Math.max(0, Math.min(canvasWidth, newX)), y: Math.max(0, Math.min(canvasHeight, newY)) });
  };

  const handleMouseUp = () => {
    setDraggingId(null);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      className="relative w-full aspect-video bg-black/60 rounded-xl overflow-hidden border border-slate-700/80 shadow-2xl select-none"
    >
      <div className="absolute inset-0 flex items-center justify-center text-slate-600 font-mono text-xs pointer-events-none">
        1920 × 1080 Canvas Preview
      </div>

      {activeLayers.map(layer => {
        const leftPct = (layer.x / canvasWidth) * 100;
        const topPct = (layer.y / canvasHeight) * 100;
        const isSelected = selectedLayerId === layer.id;

        return (
          <div
            key={layer.id}
            onMouseDown={e => handleMouseDown(e, layer)}
            style={{
              left: `${leftPct}%`,
              top: `${topPct}%`,
              opacity: layer.opacity,
              transform: `rotate(${layer.rotation}deg)`,
              color: layer.style?.color || '#ffffff',
              fontSize: `${(layer.style?.font_size || 36) * 0.4}px`,
              WebkitTextStroke: `${(layer.style?.border_width || 1) * 0.5}px ${layer.style?.border_color || '#000000'}`
            }}
            className={`absolute cursor-move px-2 py-1 transition-shadow duration-75 rounded ${
              isSelected
                ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-900 bg-indigo-500/20'
                : 'hover:ring-1 hover:ring-slate-400/50'
            }`}
          >
            <div className="font-bold whitespace-nowrap">
              {layer.text || layer.source || layer.type.toUpperCase()}
            </div>
            {isSelected && (
              <div className="absolute -top-6 left-0 text-[10px] font-mono bg-indigo-600 text-white px-1.5 py-0.5 rounded shadow">
                ({layer.x}, {layer.y})
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
