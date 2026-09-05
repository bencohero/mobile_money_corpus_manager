import subprocess
import pytest
import app.main as main
def test_audio_command_always_releases_slot(monkeypatch):
    class FakeSlots:
        def __init__(self): self.released=False
        def acquire(self, blocking=False): return True
        def release(self): self.released=True
    slots=FakeSlots()
    monkeypatch.setattr(main, "CONVERSION_SLOTS", slots)
    def fail(*args, **kwargs): raise subprocess.TimeoutExpired("ffmpeg", 1)
    monkeypatch.setattr(main.subprocess, "run", fail)
    with pytest.raises(subprocess.TimeoutExpired):
        main.run_audio_command(["ffmpeg"], timeout=1)
    assert slots.released
def test_audio_command_rejects_saturated_slot(monkeypatch):
    class FullSlots:
        def acquire(self, blocking=False): return False
    monkeypatch.setattr(main, "CONVERSION_SLOTS", FullSlots())
    with pytest.raises(main.ConversionSaturated):
        main.run_audio_command(["ffmpeg"])
def test_audio_command_never_uses_shell(monkeypatch):
    seen={}
    class Slot:
        def acquire(self, blocking=False): return True
        def release(self): pass
    def fake(*args, **kwargs):
        seen.update(kwargs); return object()
    monkeypatch.setattr(main, "CONVERSION_SLOTS", Slot())
    monkeypatch.setattr(main.subprocess, "run", fake)
    main.run_audio_command(["ffprobe"])
    assert seen["shell"] is False
