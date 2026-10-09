import os
import wave
import numpy as np

SR = 44100
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")

_SEMI = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4,
    "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
    "A#": 10, "Bb": 10, "B": 11,
}


def note_hz(note):
    if not note or note in ("-", "R"):
        return 0.0
    i = 1
    name = note[0].upper()
    if len(note) > 1 and note[1] in "#b":
        name += note[1]
        i = 2
    octave = int(note[i:])
    midi = _SEMI[name] + 12 * (octave + 1)
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def osc(phase, kind):
    if kind == "sine":
        return np.sin(phase)
    frac = (phase / (2.0 * np.pi)) % 1.0
    if kind == "triangle":
        return 4.0 * np.abs(frac - 0.5) - 1.0
    if kind == "saw":
        return 2.0 * frac - 1.0
    if kind == "square":
        return np.where(frac < 0.5, 1.0, -1.0)
    if kind == "pulse12":
        return np.where(frac < 0.125, 1.0, -1.0)
    return np.where(frac < 0.25, 1.0, -1.0)


def adsr(n, a=0.005, d=0.04, s=0.7, r=0.06, sr=SR):
    if n <= 0:
        return np.zeros(0)
    an = int(a * sr)
    dn = int(d * sr)
    rn = int(r * sr)
    if an + dn + rn > n:
        scale = n / float(an + dn + rn)
        an = int(an * scale)
        dn = int(dn * scale)
        rn = max(0, n - an - dn)
    sn = n - an - dn - rn
    parts = []
    if an:
        parts.append(np.linspace(0.0, 1.0, an, endpoint=False))
    if dn:
        parts.append(np.linspace(1.0, s, dn, endpoint=False))
    if sn:
        parts.append(np.full(sn, s))
    if rn:
        parts.append(np.linspace(s, 0.0, rn))
    env = np.concatenate(parts)
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env[:n]


def _add(buf, ev, sr=SR):
    start = int(ev["start"] * sr)
    if start >= len(buf):
        return
    n = int(ev["dur"] * sr)
    if n <= 0:
        return
    kind = ev.get("kind", "pulse")
    if kind == "noise":
        w = np.random.uniform(-1.0, 1.0, n)
    elif kind == "kick":
        f = np.linspace(ev.get("f0", 150.0), ev.get("f1", 45.0), n)
        w = np.sin(2.0 * np.pi * np.cumsum(f) / sr)
    else:
        f = note_hz(ev["note"])
        if f <= 0:
            return
        t = np.arange(n) / sr
        vib = ev.get("vib", 0.0)
        if vib:
            ft = f * (1.0 + vib * np.sin(2.0 * np.pi * 5.5 * t))
            phase = 2.0 * np.pi * np.cumsum(ft) / sr
        else:
            phase = 2.0 * np.pi * f * t
        w = osc(phase, kind)
    env = adsr(n, ev.get("a", 0.005), ev.get("d", 0.04),
               ev.get("s", 0.7), ev.get("r", 0.06), sr)
    seg = w * env * ev.get("vol", 0.2)
    end = min(len(buf), start + n)
    buf[start:end] += seg[: end - start]


def render(events, length_s, sr=SR):
    buf = np.zeros(int(length_s * sr), dtype=np.float64)
    for ev in events:
        _add(buf, ev, sr)
    return buf


def normalize(buf, peak=0.85):
    m = np.max(np.abs(buf)) if len(buf) else 0.0
    if m > 0:
        buf = buf * (peak / m)
    return buf


def write_wav(path, buf, sr=SR):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    data = np.clip(buf, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def _melody(events, seq, beat_s, start_beat=0.0, step=0.5, dur=0.44,
            kind="pulse", vol=0.2, **kw):
    b = start_beat
    for note in seq:
        if note not in ("-", ""):
            events.append({
                "note": note, "start": b * beat_s,
                "dur": max(0.03, dur) * beat_s, "kind": kind, "vol": vol, **kw,
            })
        b += step
    return b


def _drum(events, beat_s, pos, kind, vol):
    if kind == "kick":
        events.append({
            "note": "C1", "start": pos * beat_s, "dur": 0.14, "kind": "kick",
            "f0": 165.0, "f1": 45.0, "vol": vol,
            "a": 0.001, "d": 0.05, "s": 0.35, "r": 0.08,
        })
    elif kind == "tom":
        events.append({
            "note": "C2", "start": pos * beat_s, "dur": 0.16, "kind": "kick",
            "f0": 260.0, "f1": 130.0, "vol": vol,
            "a": 0.001, "d": 0.06, "s": 0.25, "r": 0.10,
        })
    elif kind == "snare":
        events.append({
            "note": "-", "start": pos * beat_s, "dur": 0.14, "kind": "noise",
            "vol": vol, "a": 0.001, "d": 0.05, "s": 0.12, "r": 0.08,
        })
    else:
        events.append({
            "note": "-", "start": pos * beat_s, "dur": 0.045, "kind": "noise",
            "vol": vol, "a": 0.001, "d": 0.02, "s": 0.0, "r": 0.02,
        })


def game_music():
    bpm = 152.0
    beat = 60.0 / bpm
    bars = 8
    total = bars * 4 * beat
    ev = []
    lead = (
        "C5 E5 G5 E5 A5 G5 E5 C5 "
        "F5 A5 C6 A5 G5 E5 C5 E5 "
        "D5 F5 A5 F5 B5 A5 F5 D5 "
        "E5 G5 C6 B5 C6 - - - "
        "E5 E5 G5 A5 G5 E5 C5 D5 "
        "F5 F5 A5 B5 A5 F5 D5 C5 "
        "G5 A5 B5 C6 D6 C6 B5 A5 "
        "G5 E5 C5 - C5 - - -"
    ).split()
    _melody(ev, lead, beat, 0.0, step=0.5, dur=0.44, kind="pulse",
            vol=0.20, vib=0.006)
    fifth = {"C3": "G3", "F3": "C4", "D3": "A3", "G3": "D4"}
    roots = ["C3", "F3", "D3", "C3", "C3", "F3", "G3", "C3"]
    for i, root in enumerate(roots):
        base = i * 4
        pattern = [root, root, fifth[root], root, root, root, fifth[root], root]
        for j, note in enumerate(pattern):
            _melody(ev, [note], beat, base + j * 0.5, step=0.5, dur=0.42,
                    kind="triangle", vol=0.24)
    for i in range(bars):
        base = i * 4
        _drum(ev, beat, base + 0.0, "kick", 0.55)
        _drum(ev, beat, base + 2.0, "kick", 0.5)
        _drum(ev, beat, base + 1.0, "snare", 0.30)
        _drum(ev, beat, base + 3.0, "snare", 0.30)
        for j in range(8):
            _drum(ev, beat, base + j * 0.5, "hat", 0.11)
    return render(ev, total)


def menu_music():
    bpm = 126.0
    beat = 60.0 / bpm
    bars = 8
    total = bars * 3 * beat
    ev = []
    mel = (
        "G4 B4 D5 E5 C5 A4 F4 A4 C5 D5 B4 G4 "
        "C5 E5 G5 A5 E5 C5 F#5 D5 A4 G5 D5 B4"
    ).split()
    _melody(ev, mel, beat, 0.0, step=1.0, dur=0.85, kind="pulse12",
            vol=0.19, vib=0.008)
    chords = {
        "C3": ["E4", "G4"], "A2": ["C4", "E4"], "F2": ["A3", "C4"],
        "G2": ["B3", "D4"], "D3": ["F#4", "A4"],
    }
    roots = ["C3", "A2", "F2", "G2", "C3", "A2", "D3", "G2"]
    for i, root in enumerate(roots):
        base = i * 3
        _melody(ev, [root], beat, base, step=1.0, dur=0.7,
                kind="triangle", vol=0.26)
        for b in (1.0, 2.0):
            for tone in chords[root]:
                _melody(ev, [tone], beat, base + b, step=1.0, dur=0.35,
                        kind="pulse12", vol=0.10)
    return render(ev, total)


def boss_music():
    bpm = 144.0
    beat = 60.0 / bpm
    bars = 8
    total = bars * 4 * beat
    ev = []
    lead = (
        "A4 C5 E5 C5 A4 C5 E5 A5 "
        "F4 A4 C5 A4 F4 A4 C5 F5 "
        "G4 B4 D5 B4 G4 B4 D5 G5 "
        "E4 G#4 B4 G#4 E4 G#4 B4 E5 "
        "A4 C5 E5 A5 C6 B5 A5 G5 "
        "F5 E5 D5 C5 D5 E5 F5 G5 "
        "G5 F5 E5 D5 E5 F5 G5 B5 "
        "E5 D#5 E5 B4 G#4 E4 B4 E5"
    ).split()
    _melody(ev, lead, beat, 0.0, step=0.5, dur=0.42, kind="pulse",
            vol=0.20, vib=0.007)
    root_hi = {"A2": "A3", "F2": "F3", "G2": "G3", "E2": "E3"}
    roots = ["A2", "F2", "G2", "E2", "A2", "F2", "G2", "E2"]
    for i, root in enumerate(roots):
        base = i * 4
        hi = root_hi[root]
        pattern = [root, root, hi, root, root, root, hi, root]
        for j, note in enumerate(pattern):
            _melody(ev, [note], beat, base + j * 0.5, step=0.5, dur=0.40,
                    kind="saw", vol=0.19)
            _melody(ev, [note], beat, base + j * 0.5, step=0.5, dur=0.36,
                    kind="square", vol=0.07)
    for i in range(bars):
        base = i * 4
        _drum(ev, beat, base + 0.0, "kick", 0.60)
        _drum(ev, beat, base + 1.5, "kick", 0.45)
        _drum(ev, beat, base + 2.0, "kick", 0.55)
        _drum(ev, beat, base + 1.0, "snare", 0.35)
        _drum(ev, beat, base + 3.0, "snare", 0.35)
        _drum(ev, beat, base + 3.5, "snare", 0.18)
        for j in range(8):
            _drum(ev, beat, base + j * 0.5, "hat", 0.10)
        if i % 4 == 3:
            _drum(ev, beat, base + 2.5, "tom", 0.42)
            _drum(ev, beat, base + 3.0, "tom", 0.42)
            _drum(ev, beat, base + 3.5, "tom", 0.42)
    return render(ev, total)


def _tone(note, dur, kind="pulse", vol=0.32):
    n = int(dur * SR)
    hz = note_hz(note)
    t = np.arange(n) / SR
    w = osc(2.0 * np.pi * hz * t, kind)
    return w * adsr(n, 0.004, 0.03, 0.6, 0.05) * vol


def _sweep(f0, f1, dur, kind="square", a=0.004, d=0.05, s=0.5, r=0.06):
    n = int(dur * SR)
    f = np.linspace(f0, f1, n)
    w = osc(2.0 * np.pi * np.cumsum(f) / SR, kind)
    return w * adsr(n, a, d, s, r)


def sfx_jump():
    return _sweep(320.0, 780.0, 0.18, "pulse", s=0.5) * 0.42


def sfx_coin():
    return np.concatenate([_tone("B5", 0.06), _tone("E6", 0.16)])


def sfx_stomp():
    n = int(0.17 * SR)
    f = np.linspace(520.0, 110.0, n)
    body = osc(2.0 * np.pi * np.cumsum(f) / SR, "square")
    body = body * adsr(n, 0.002, 0.05, 0.3, 0.06) * 0.35
    noise = np.random.uniform(-1.0, 1.0, n) * np.linspace(1.0, 0.0, n) * 0.2
    return body + noise


def sfx_bump():
    n = int(0.12 * SR)
    f = np.linspace(190.0, 70.0, n)
    w = np.sin(2.0 * np.pi * np.cumsum(f) / SR)
    return w * adsr(n, 0.002, 0.04, 0.2, 0.05) * 0.45


def sfx_powerup():
    parts = [_tone(x, 0.075) for x in ("C5", "E5", "G5", "C6", "E6", "G6")]
    return np.concatenate(parts)


def sfx_hurt():
    n = int(0.42 * SR)
    f = np.linspace(620.0, 110.0, n)
    w = osc(2.0 * np.pi * np.cumsum(f) / SR, "square")
    return w * adsr(n, 0.005, 0.15, 0.4, 0.2) * 0.4


def sfx_win():
    parts = [_tone(nn, dd) for nn, dd in
             (("C5", 0.12), ("E5", 0.12), ("G5", 0.12), ("C6", 0.42))]
    chord = (_tone("C6", 0.5, "triangle", 0.20)
             + _tone("E6", 0.5, "triangle", 0.15)
             + _tone("G6", 0.5, "triangle", 0.12))
    return np.concatenate(parts + [chord])


def sfx_life():
    parts = [_tone(x, 0.09) for x in ("C6", "E6", "G6", "C6", "E6", "G6")]
    return np.concatenate(parts)


def sfx_checkpoint():
    parts = [_tone(x, 0.10) for x in ("G5", "C6", "E6", "G6")]
    return np.concatenate(parts)


_JOBS = {
    "music_game.wav": (game_music, 0.80),
    "music_menu.wav": (menu_music, 0.72),
    "music_boss.wav": (boss_music, 0.82),
    "sfx_jump.wav": (sfx_jump, 0.75),
    "sfx_coin.wav": (sfx_coin, 0.70),
    "sfx_stomp.wav": (sfx_stomp, 0.75),
    "sfx_bump.wav": (sfx_bump, 0.80),
    "sfx_powerup.wav": (sfx_powerup, 0.70),
    "sfx_hurt.wav": (sfx_hurt, 0.75),
    "sfx_win.wav": (sfx_win, 0.72),
    "sfx_life.wav": (sfx_life, 0.68),
    "sfx_checkpoint.wav": (sfx_checkpoint, 0.70),
}


def ensure_assets(verbose=False):
    made = []
    for name, (builder, peak) in _JOBS.items():
        path = os.path.join(ASSETS, name)
        if os.path.exists(path):
            continue
        write_wav(path, normalize(builder(), peak))
        made.append(name)
        if verbose:
            print("generated", name)
    return made


def main():
    made = ensure_assets(verbose=True)
    if made:
        print("Wrote %d audio files to %s" % (len(made), ASSETS))
    else:
        print("All audio assets already exist in %s" % ASSETS)


if __name__ == "__main__":
    main()
