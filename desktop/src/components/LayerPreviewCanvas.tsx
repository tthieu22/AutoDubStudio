import React, { useState, useRef, useEffect } from 'react';

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
  onSelectLayer: (id: string | null) => void;
  onUpdateLayer: (updated: CanvasLayer, pushHistory?: boolean) => void;
  currentTime: number;
  canvasWidth?: number;
  canvasHeight?: number;
}

interface InteractionState {
  type: 'move' | 'resize';
  handle?: 'tl' | 'tr' | 'bl' | 'br';
  initialX: number;
  initialY: number;
  initialWidth: number;
  initialHeight: number;
  startClientX: number;
  startClientY: number;
  layer: CanvasLayer;
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
  const [interaction, setInteraction] = useState<InteractionState | null>(null);

  const activeLayers = layers
    .filter(l => l.visible && (l.duration === 0 || (currentTime >= l.start && currentTime <= l.start + l.duration)))
    .sort((a, b) => a.z_index - b.z_index);

  const selectedLayer = layers.find(l => l.id === selectedLayerId);
  const isSelectedLayerActive = selectedLayer && 
    (selectedLayer.duration === 0 || (currentTime >= selectedLayer.start && currentTime <= selectedLayer.start + selectedLayer.duration));

  // Handle document-level mouse move and mouse up for flawless dragging & single-history commits
  useEffect(() => {
    if (!interaction) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const scaleX = canvasWidth / rect.width;
      const scaleY = canvasHeight / rect.height;
      
      const deltaX = (e.clientX - interaction.startClientX) * scaleX;
      const deltaY = (e.clientY - interaction.startClientY) * scaleY;

      const layer = interaction.layer;
      const initW = interaction.initialWidth;
      const initH = interaction.initialHeight;
      const initX = interaction.initialX;
      const initY = interaction.initialY;

      if (interaction.type === 'move') {
        if (layer.locked) return;
        const newX = Math.round(initX + deltaX);
        const newY = Math.round(initY + deltaY);
        
        onUpdateLayer({
          ...layer,
          x: Math.max(-initW, Math.min(canvasWidth, newX)),
          y: Math.max(-initH, Math.min(canvasHeight, newY))
        }, false); // Do not push to history yet
      } else if (interaction.type === 'resize' && interaction.handle) {
        if (layer.locked) return;
        
        const handle = interaction.handle;
        const aspect = initW / initH;
        const isAspectLocked = ['logo', 'image', 'video'].includes(layer.type);
        const minSize = 20;

        let newW = initW;
        let newH = initH;
        let newX = initX;
        let newY = initY;

        // Calculate size based on opposite anchors
        if (handle === 'br') {
          // Opposite anchor: Top-Left (initX, initY)
          newW = initW + deltaX;
          newH = isAspectLocked ? newW / aspect : initH + deltaY;
          if (newW < minSize) {
            newW = minSize;
            newH = isAspectLocked ? newW / aspect : newH;
          }
          if (newH < minSize) {
            newH = minSize;
            newW = isAspectLocked ? newH * aspect : newW;
          }
        } else if (handle === 'bl') {
          // Opposite anchor: Top-Right (initX + initW, initY)
          newW = initW - deltaX;
          newH = isAspectLocked ? newW / aspect : initH + deltaY;
          if (newW < minSize) {
            newW = minSize;
            newH = isAspectLocked ? newW / aspect : newH;
          }
          if (newH < minSize) {
            newH = minSize;
            newW = isAspectLocked ? newH * aspect : newW;
          }
          newX = (initX + initW) - newW;
        } else if (handle === 'tr') {
          // Opposite anchor: Bottom-Left (initX, initY + initH)
          newW = initW + deltaX;
          newH = isAspectLocked ? newW / aspect : initH - deltaY;
          if (newW < minSize) {
            newW = minSize;
            newH = isAspectLocked ? newW / aspect : newH;
          }
          if (newH < minSize) {
            newH = minSize;
            newW = isAspectLocked ? newH * aspect : newW;
          }
          newY = (initY + initH) - newH;
        } else if (handle === 'tl') {
          // Opposite anchor: Bottom-Right (initX + initW, initY + initH)
          newW = initW - deltaX;
          newH = isAspectLocked ? newW / aspect : initH - deltaY;
          if (newW < minSize) {
            newW = minSize;
            newH = isAspectLocked ? newW / aspect : newH;
          }
          if (newH < minSize) {
            newH = minSize;
            newW = isAspectLocked ? newH * aspect : newW;
          }
          newX = (initX + initW) - newW;
          newY = (initY + initH) - newH;
        }

        onUpdateLayer({
          ...layer,
          x: Math.round(newX),
          y: Math.round(newY),
          width: Math.round(newW),
          height: Math.round(newH)
        }, false); // Do not push to history yet
      }
    };

    const handleMouseUp = () => {
      // Commit final state to parent and push to history
      if (containerRef.current) {
        const currentLayerState = layers.find(l => l.id === interaction.layer.id);
        if (currentLayerState) {
          onUpdateLayer(currentLayerState, true); // Push to history now
        }
      }
      setInteraction(null);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [interaction, layers, onUpdateLayer, canvasWidth, canvasHeight]);

  const handleMouseDown = (e: React.MouseEvent, layer: CanvasLayer) => {
    e.stopPropagation();
    onSelectLayer(layer.id);
    if (layer.locked) return;

    const currentW = layer.width !== undefined ? layer.width : (layer.type === 'video' ? canvasWidth : 400);
    const currentH = layer.height !== undefined ? layer.height : (layer.type === 'video' ? canvasHeight : (layer.type === 'logo' || layer.type === 'image' ? 225 : 100));

    setInteraction({
      type: 'move',
      initialX: layer.x,
      initialY: layer.y,
      initialWidth: currentW,
      initialHeight: currentH,
      startClientX: e.clientX,
      startClientY: e.clientY,
      layer
    });
  };

  const handleResizeStart = (e: React.MouseEvent, handle: 'tl' | 'tr' | 'bl' | 'br', layer: CanvasLayer) => {
    e.stopPropagation();
    e.preventDefault();
    if (layer.locked) return;

    const currentW = layer.width !== undefined ? layer.width : (layer.type === 'video' ? canvasWidth : 400);
    const currentH = layer.height !== undefined ? layer.height : (layer.type === 'video' ? canvasHeight : (layer.type === 'logo' || layer.type === 'image' ? 225 : 100));

    setInteraction({
      type: 'resize',
      handle,
      initialX: layer.x,
      initialY: layer.y,
      initialWidth: currentW,
      initialHeight: currentH,
      startClientX: e.clientX,
      startClientY: e.clientY,
      layer
    });
  };

  const handleCanvasClick = (e: React.MouseEvent) => {
    // Click outside layers deselects
    if (e.target === containerRef.current) {
      onSelectLayer(null);
    }
  };

  return (
    <div
      ref={containerRef}
      onMouseDown={handleCanvasClick}
      style={{ aspectRatio: `${canvasWidth} / ${canvasHeight}` }}
      className="relative w-full bg-black/60 rounded-xl overflow-hidden border border-slate-700/80 shadow-2xl select-none"
    >
      <div className="absolute inset-0 flex items-center justify-center text-slate-600 font-mono text-xs pointer-events-none">
        {canvasWidth} × {canvasHeight} Canvas Preview
      </div>

      {activeLayers.map(layer => {
        const leftPct = (layer.x / canvasWidth) * 100;
        const topPct = (layer.y / canvasHeight) * 100;
        
        const resolvedW = layer.width !== undefined ? layer.width : (layer.type === 'video' ? canvasWidth : 400);
        const resolvedH = layer.height !== undefined ? layer.height : (layer.type === 'video' ? canvasHeight : (layer.type === 'logo' || layer.type === 'image' ? 225 : 100));
        
        const widthPct = `${(resolvedW / canvasWidth) * 100}%`;
        const heightPct = `${(resolvedH / canvasHeight) * 100}%`;
        const isSelected = selectedLayerId === layer.id;

        return (
          <div
            key={layer.id}
            onMouseDown={e => handleMouseDown(e, layer)}
            style={{
              left: `${leftPct}%`,
              top: `${topPct}%`,
              width: widthPct,
              height: heightPct,
              opacity: layer.opacity,
              transform: `rotate(${layer.rotation}deg)`,
              color: layer.style?.color || '#ffffff',
              fontSize: `${(layer.style?.font_size || 36) * 0.4}px`,
              WebkitTextStroke: `${(layer.style?.border_width || 1) * 0.5}px ${layer.style?.border_color || '#000000'}`
            }}
            className={`absolute transition-shadow duration-75 rounded flex items-center justify-center ${
              layer.locked ? 'cursor-default' : 'cursor-move'
            } ${
              isSelected
                ? 'ring-2 ring-emerald-500/80 bg-emerald-500/10'
                : 'hover:ring-1 hover:ring-slate-400/50'
            }`}
          >
            <div className="font-bold whitespace-nowrap p-2 select-none">
              {layer.text || layer.source || layer.type.toUpperCase()}
            </div>

            {/* Transform Handles Overlay for the selected layer */}
            {isSelected && (
              <>
                <div className="absolute inset-0 border border-emerald-400 pointer-events-none" />
                
                {/* Visual coordinate badge */}
                <div className="absolute -top-6 left-0 text-[10px] font-mono bg-emerald-600 text-white px-1.5 py-0.5 rounded shadow whitespace-nowrap z-50 pointer-events-none">
                  Pos: ({layer.x}, {layer.y}) | Size: {layer.width || 'auto'}x{layer.height || 'auto'}
                </div>

                {/* Handles (hidden if layer is locked) */}
                {!layer.locked && (
                  <>
                    {/* Top-Left */}
                    <div
                      onMouseDown={e => handleResizeStart(e, 'tl', layer)}
                      className="absolute -top-1 -left-1 w-3 h-3 bg-white border-2 border-emerald-500 rounded-full cursor-nwse-resize shadow z-50 hover:bg-emerald-100 transition-colors"
                    />
                    {/* Top-Right */}
                    <div
                      onMouseDown={e => handleResizeStart(e, 'tr', layer)}
                      className="absolute -top-1 -right-1 w-3 h-3 bg-white border-2 border-emerald-500 rounded-full cursor-nesw-resize shadow z-50 hover:bg-emerald-100 transition-colors"
                    />
                    {/* Bottom-Left */}
                    <div
                      onMouseDown={e => handleResizeStart(e, 'bl', layer)}
                      className="absolute -bottom-1 -left-1 w-3 h-3 bg-white border-2 border-emerald-500 rounded-full cursor-nesw-resize shadow z-50 hover:bg-emerald-100 transition-colors"
                    />
                    {/* Bottom-Right */}
                    <div
                      onMouseDown={e => handleResizeStart(e, 'br', layer)}
                      className="absolute -bottom-1 -right-1 w-3 h-3 bg-white border-2 border-emerald-500 rounded-full cursor-nwse-resize shadow z-50 hover:bg-emerald-100 transition-colors"
                    />
                  </>
                )}
              </>
            )}
          </div>
        );
      })}
    </div>
  );
};
