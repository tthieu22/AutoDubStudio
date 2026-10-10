import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { VideoCanvas } from './VideoCanvas';
import { editorStore } from '../../editor/state/editorStore';

// Mock Tauri convertFileSrc
vi.mock('@tauri-apps/api/tauri', () => ({
  convertFileSrc: (path: string) => `converted-url://${path}`,
}));

describe('VideoCanvas Component', () => {
  const dummyComposition = {
    id: 'test-project-dir',
    name: 'Test Project',
    width: 1920,
    height: 1080,
    fps: 30,
    duration: 120,
    tracks: [],
    clips: [
      {
        id: 'clip-video-source',
        name: 'Original Video',
        type: 'video',
        trackId: 'track-video-main',
        startTime: 0,
        duration: 120,
        visible: true,
        locked: false,
        opacity: 1,
        zIndex: 1,
        x: 50,
        y: 50,
        width: 100,
        height: 100,
        rotation: 0,
        scaleX: 1,
        scaleY: 1,
        videoProps: {
          src: 'source/input.mp4',
          volume: 1,
          muted: false,
          playbackRate: 1,
        },
      },
    ],
  };

  it('renders video element with correct source in mockup mode', () => {
    // Override window.__TAURI_IPC__ to simulate browser mode
    const originalIpc = (window as any).__TAURI_IPC__;
    delete (window as any).__TAURI_IPC__;

    const { container } = render(
      <VideoCanvas
        composition={dummyComposition as any}
        selectedClipIds={[]}
        showSafeArea={false}
        currentTime={0}
        isPlaying={false}
      />
    );

    const videoEl = container.querySelector('video');
    expect(videoEl).toBeInTheDocument();
    expect(videoEl?.src).toBe('https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4');

    (window as any).__TAURI_IPC__ = originalIpc;
  });

  it('renders video element with converted Tauri path when in Tauri mode', () => {
    // Mock Tauri IPC
    (window as any).__TAURI_IPC__ = () => {};

    const { container } = render(
      <VideoCanvas
        composition={dummyComposition as any}
        selectedClipIds={[]}
        showSafeArea={false}
        currentTime={0}
        isPlaying={false}
      />
    );

    const videoEl = container.querySelector('video');
    expect(videoEl).toBeInTheDocument();
    expect(videoEl?.src).toContain('converted-url://test-project-dir/source/input.mp4');

    delete (window as any).__TAURI_IPC__;
  });

  it('displays friendly message if source video is missing in Tauri mode', () => {
    (window as any).__TAURI_IPC__ = () => {};
    const noVideoComp = { ...dummyComposition, clips: [] };

    render(
      <VideoCanvas
        composition={noVideoComp as any}
        selectedClipIds={[]}
        showSafeArea={false}
        currentTime={0}
        isPlaying={false}
      />
    );

    expect(screen.getByText('No source video available')).toBeInTheDocument();
    delete (window as any).__TAURI_IPC__;
  });
});
