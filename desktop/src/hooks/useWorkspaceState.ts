import { useState, useEffect, useCallback } from 'react';
import { PipelineMode } from '../types/pipeline';

export interface WorkspaceState {
  sidebarWidth: number;
  inspectorWidth: number;
  bottomPanelHeight: number;
  isSidebarCollapsed: boolean;
  isInspectorCollapsed: boolean;
  isBottomPanelCollapsed: boolean;
  pipelineMode: PipelineMode;
  timelineZoom: number;
  activeInspectorTab: string;
}

const STORAGE_KEY = 'autodub_v02_workspace_state';

const DEFAULT_STATE: WorkspaceState = {
  sidebarWidth: 240,
  inspectorWidth: 320,
  bottomPanelHeight: 280,
  isSidebarCollapsed: false,
  isInspectorCollapsed: false,
  isBottomPanelCollapsed: false,
  pipelineMode: 'STORY',
  timelineZoom: 1,
  activeInspectorTab: 'general'
};

export function useWorkspaceState() {
  const [state, setState] = useState<WorkspaceState>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return { ...DEFAULT_STATE, ...JSON.parse(saved) };
      }
    } catch (e) {
      console.warn('Failed to parse saved workspace state:', e);
    }
    return DEFAULT_STATE;
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      console.warn('Failed to persist workspace state:', e);
    }
  }, [state]);

  const setSidebarWidth = useCallback((width: number) => {
    const clamped = Math.max(160, Math.min(420, width));
    setState(prev => ({ ...prev, sidebarWidth: clamped }));
  }, []);

  const setInspectorWidth = useCallback((width: number) => {
    const clamped = Math.max(220, Math.min(520, width));
    setState(prev => ({ ...prev, inspectorWidth: clamped }));
  }, []);

  const setBottomPanelHeight = useCallback((height: number) => {
    const clamped = Math.max(140, Math.min(650, height));
    setState(prev => ({ ...prev, bottomPanelHeight: clamped }));
  }, []);

  const toggleSidebar = useCallback(() => {
    setState(prev => ({ ...prev, isSidebarCollapsed: !prev.isSidebarCollapsed }));
  }, []);

  const toggleInspector = useCallback(() => {
    setState(prev => ({ ...prev, isInspectorCollapsed: !prev.isInspectorCollapsed }));
  }, []);

  const toggleBottomPanel = useCallback(() => {
    setState(prev => ({ ...prev, isBottomPanelCollapsed: !prev.isBottomPanelCollapsed }));
  }, []);

  const setPipelineMode = useCallback((mode: PipelineMode) => {
    setState(prev => ({ ...prev, pipelineMode: mode }));
  }, []);

  const setTimelineZoom = useCallback((zoom: number) => {
    const clamped = Math.max(0.2, Math.min(5, zoom));
    setState(prev => ({ ...prev, timelineZoom: clamped }));
  }, []);

  const setActiveInspectorTab = useCallback((tab: string) => {
    setState(prev => ({ ...prev, activeInspectorTab: tab }));
  }, []);

  return {
    ...state,
    setSidebarWidth,
    setInspectorWidth,
    setBottomPanelHeight,
    toggleSidebar,
    toggleInspector,
    toggleBottomPanel,
    setPipelineMode,
    setTimelineZoom,
    setActiveInspectorTab
  };
}
