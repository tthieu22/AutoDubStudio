from pathlib import Path
from autodub.modules.narration import TextNormalizer, SentenceGrouper, NaturalPacingEngine, NarrationSegment

def test_text_normalization():
    raw_text = "ANH TA...   bước vào phòng\n\nvà nhìn xung quanh [music]!!!"
    clean = TextNormalizer.normalize(raw_text)
    assert "ANH TA..." in clean
    assert "bước vào phòng" in clean
    assert "music" not in clean

def test_sentence_grouping():
    raw_segments = [
        {"id": 1, "start": 0.0, "end": 2.5, "text": "Anh ta bước vào căn phòng"},
        {"id": 2, "start": 2.5, "end": 5.0, "text": "và nhìn xung quanh."},
        {"id": 3, "start": 5.0, "end": 8.0, "text": "Không có ai ở đó."}
    ]
    grouper = SentenceGrouper(max_chars_per_chunk=250)
    narration_segments = grouper.group_segments(raw_segments)
    
    assert len(narration_segments) == 2
    assert narration_segments[0].text == "Anh ta bước vào căn phòng và nhìn xung quanh."
    assert narration_segments[0].target_start_time == 0.0
    assert narration_segments[0].target_end_time == 5.0
    assert narration_segments[1].text == "Không có ai ở đó."

def test_natural_pacing_engine():
    pacing = NaturalPacingEngine(min_speed=0.95, max_speed=1.05)
    
    # Case 1: Audio finishes early -> keep 1.0x speed and add trailing silence
    speed, final_dur, trailing_silence, mode = pacing.evaluate_pacing(
        natural_audio_duration=3.8,
        target_available_duration=4.5,
        text="Anh ta nhìn xung quanh."
    )
    assert speed == 1.0
    assert final_dur == 3.8
    assert trailing_silence >= 350
    assert mode == "natural_with_silence"

    # Case 2: Audio slightly longer -> slight speed adjustment (<= 1.05x)
    speed, final_dur, trailing_silence, mode = pacing.evaluate_pacing(
        natural_audio_duration=4.2,
        target_available_duration=4.0,
        text="Anh ta nhìn xung quanh."
    )
    assert 1.0 <= speed <= 1.05
    assert mode == "slight_speed_adjustment"

    # Case 3: Audio much longer -> clamp speed to 1.05x and allow flexible end duration
    speed, final_dur, trailing_silence, mode = pacing.evaluate_pacing(
        natural_audio_duration=6.0,
        target_available_duration=4.0,
        text="Anh ta nhìn xung quanh."
    )
    assert speed == 1.05
    assert final_dur == round(6.0 / 1.05, 3)
    assert mode == "time_stretch"
