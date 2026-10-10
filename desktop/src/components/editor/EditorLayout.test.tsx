import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { EditorLayout } from './EditorLayout';
import { editorStore } from '../../editor/state/editorStore';

describe('EditorLayout Component', () => {
  beforeEach(() => {
    editorStore.clearSelection();
  });

  it('renders top toolbar brand and title', () => {
    render(<EditorLayout />);
    expect(screen.getByText('AutoDubStudio')).toBeInTheDocument();
    expect(screen.getByText('Render / Export')).toBeInTheDocument();
  });

  it('allows adding a new text layer', () => {
    render(<EditorLayout />);
    
    // Switch to Text tab
    const textTabBtn = screen.getByTitle('Text & Titles (Ấn để ẩn/hiện panel)');
    fireEvent.click(textTabBtn);

    // Click Add Text Layer
    const addTextBtn = screen.getByText('+ Thêm Layer Chữ (Text)');
    fireEvent.click(addTextBtn);

    const comp = editorStore.getComposition();
    const hasNewText = comp.clips.some((c) => c.name === 'Text Layer');
    expect(hasNewText).toBe(true);
  });
});
