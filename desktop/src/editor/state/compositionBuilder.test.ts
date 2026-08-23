import { describe, it, expect } from 'vitest';
import { CompositionBuilder, ProjectArtifacts } from './compositionBuilder';

describe('CompositionBuilder — AI Pipeline to Timeline Integration', () => {
  it('maps STT/Translation subtitle segments directly into timeline clips', () => {
    const artifacts: ProjectArtifacts = {
      projectId: 'proj-1',
      projectName: 'Test Video Dubbing',
      videoDuration: 100,
      segments: [
        { id: 1, start: 0, end: 4, text: 'Xin chào mọi người' },
        { id: 2, start: 4, end: 8, text: 'Hôm nay chúng ta cùng học video editor' },
        { id: 3, start: 8, end: 12, text: 'AutoDubStudio' },
      ],
      dubbedAudioPath: 'audio/dubbed.wav',
      dubbedAudioDuration: 12,
    };

    const comp = CompositionBuilder.buildFromArtifacts(artifacts);

    // Verify Project Details
    expect(comp.id).toBe('proj-1');
    expect(comp.name).toBe('Test Video Dubbing');

    // Verify Video Track Clip
    const videoClip = comp.clips.find(c => c.type === 'video');
    expect(videoClip).toBeDefined();
    expect(videoClip?.duration).toBe(100);

    // Verify Dubbed Audio Segment Clips do not exist standalone
    const audioClips = comp.clips.filter(c => c.type === 'audio');
    expect(audioClips.length).toBe(0);

    // Verify Subtitle Clips have linked audioProps and segmentId
    const subClips = comp.clips.filter(c => c.type === 'subtitle');
    expect(subClips.length).toBe(3);
    
    expect(subClips[0].segmentId).toBe(1);
    expect(subClips[0].subtitleProps?.text).toBe('Xin chào mọi người');
    expect(subClips[0].audioProps?.src).toBe('audio/synced/000001.wav');
    expect(subClips[0].startTime).toBe(0);
    expect(subClips[0].duration).toBe(4);
    
    expect(subClips[1].segmentId).toBe(2);
    expect(subClips[1].subtitleProps?.text).toBe('Hôm nay chúng ta cùng học video editor');
    expect(subClips[1].audioProps?.src).toBe('audio/synced/000002.wav');
  });
});
