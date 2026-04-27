"""
Generación procedural de audio WAV en memoria usando NumPy.
Sin dependencias externas (solo numpy + wave de stdlib).

Uso:
    from audio_gen import (
        generate_bg_tension_wav,
        generate_correct_wav,
        generate_wrong_wav,
        generate_win_wav,
        generate_lose_wav,
    )
    wav_bytes = generate_bg_tension_wav()  # bytes WAV listos para st.audio
"""
import io
import wave
import numpy as np

SAMPLE_RATE = 44100


def _to_wav_bytes(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Convierte un array float32 [-1, 1] a bytes WAV mono 16-bit."""
    # Normalizar a -1..1 con margen de seguridad
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.85
    # Convertir a int16
    audio_int16 = (audio * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    return buffer.getvalue()


def _adsr(num_samples: int, attack: float = 0.01, release: float = 0.1,
          sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Envolvente ADSR simple: ataque rápido, sostenido plano, liberación."""
    env = np.ones(num_samples)
    a_samples = int(attack * sample_rate)
    r_samples = int(release * sample_rate)
    if a_samples > 0:
        env[:a_samples] = np.linspace(0, 1, a_samples)
    if r_samples > 0 and r_samples < num_samples:
        env[-r_samples:] = np.linspace(1, 0, r_samples)
    return env


def _sawtooth(freq: float, t: np.ndarray) -> np.ndarray:
    """Onda diente de sierra a partir de senos (banda limitada simple)."""
    out = np.zeros_like(t)
    n = 1
    while freq * n < SAMPLE_RATE / 2 and n <= 30:
        out += np.sin(2 * np.pi * freq * n * t) / n
        n += 1
    return out * (2 / np.pi)


def _lowpass_simple(signal: np.ndarray, cutoff_norm: float) -> np.ndarray:
    """Filtro pasa-bajos de 1er orden (RC simple). cutoff_norm en [0, 1]."""
    alpha = max(0.001, min(0.999, cutoff_norm))
    out = np.zeros_like(signal)
    out[0] = signal[0] * alpha
    for i in range(1, len(signal)):
        out[i] = out[i - 1] + alpha * (signal[i] - out[i - 1])
    return out


# ============================================================
# MÚSICA DE FONDO DE TENSIÓN (loop perfecto)
# ============================================================
def generate_bg_tension_wav(duration: float = 16.0) -> bytes:
    """
    Genera un loop de música de tensión.
    Capas: drone bajo + tritono + latido cardiaco + cuerda aguda + stingers ocasionales.
    El loop es de 16 segundos para que sea fluido al repetirse.
    """
    num_samples = int(duration * SAMPLE_RATE)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # CAPA 1: Drone bajo (La1, 55Hz) sawtooth filtrado
    drone_freq = 55.0
    drone_raw = _sawtooth(drone_freq, t)
    # LFO lento que modula el corte del filtro (efecto "respira")
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t)
    cutoff = 0.005 + 0.015 * lfo  # entre 0.005 y 0.020
    drone = np.zeros_like(drone_raw)
    state = 0.0
    for i in range(num_samples):
        state = state + cutoff[i] * (drone_raw[i] - state)
        drone[i] = state
    drone *= 0.55

    # CAPA 2: Tritono (intervalo del diablo: 55 * sqrt(2) ≈ 77.78Hz)
    tritone_freq = 55.0 * np.sqrt(2)
    tritone = 0.18 * np.sin(2 * np.pi * tritone_freq * t)

    # CAPA 3: Cuerda aguda sostenida (La4, filtrada)
    high_string = 0.06 * _sawtooth(440.0, t)
    # Modulación de amplitud lenta (entra y sale)
    high_mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)
    high_string *= high_mod

    # CAPA 4: Latidos cardíacos (lub-dub a ~60 BPM = 1 latido/seg)
    heartbeat = np.zeros_like(t)
    bpm = 60
    beat_interval = 60.0 / bpm
    beat_count = int(duration / beat_interval)
    for k in range(beat_count):
        for j, vol in enumerate([0.7, 0.45]):  # lub-dub
            t0 = k * beat_interval + j * 0.14
            if t0 >= duration:
                continue
            beat_dur = 0.18
            beat_samples = int(beat_dur * SAMPLE_RATE)
            start_idx = int(t0 * SAMPLE_RATE)
            end_idx = min(start_idx + beat_samples, num_samples)
            n = end_idx - start_idx
            if n <= 0:
                continue
            tt = np.linspace(0, beat_dur, n)
            # Frecuencia que cae de 80Hz a 28Hz exponencialmente (kick drum)
            freq_curve = 80 * np.exp(-tt / 0.04) + 28 * (1 - np.exp(-tt / 0.04))
            phase = 2 * np.pi * np.cumsum(freq_curve) / SAMPLE_RATE
            beat_wave = np.sin(phase)
            # Envolvente: ataque inmediato, decay exponencial
            envelope = vol * np.exp(-tt / 0.05)
            heartbeat[start_idx:end_idx] += beat_wave * envelope

    # CAPA 5: Stingers ocasionales (cluster disonante agudo)
    stingers = np.zeros_like(t)
    stinger_times = [3.5, 9.8]  # 2 stingers en los 16 segundos
    for st_time in stinger_times:
        if st_time >= duration:
            continue
        st_dur = 0.9
        st_samples = int(st_dur * SAMPLE_RATE)
        start_idx = int(st_time * SAMPLE_RATE)
        end_idx = min(start_idx + st_samples, num_samples)
        n = end_idx - start_idx
        if n <= 0:
            continue
        tt = np.linspace(0, st_dur, n)
        # Cluster disonante: A5, Bb5, Eb6
        cluster = (
            np.sin(2 * np.pi * 880 * tt) +
            np.sin(2 * np.pi * 932.33 * tt) +
            np.sin(2 * np.pi * 1244.51 * tt)
        ) / 3
        # Envolvente: sube rápido, baja lento
        env = np.exp(-tt / 0.4) * (1 - np.exp(-tt / 0.04))
        stingers[start_idx:end_idx] += 0.18 * cluster * env

    # Mezcla final
    audio = drone + tritone + high_string + heartbeat + stingers

    # Crossfade en los extremos para que el loop sea perfecto
    fade_samples = int(0.05 * SAMPLE_RATE)
    if fade_samples > 0:
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        audio[:fade_samples] *= fade_in
        audio[-fade_samples:] *= fade_out

    return _to_wav_bytes(audio)


# ============================================================
# EFECTOS PUNTUALES
# ============================================================
def generate_click_wav() -> bytes:
    """Clic suave al presionar tecla."""
    duration = 0.04
    num_samples = int(duration * SAMPLE_RATE)
    t = np.linspace(0, duration, num_samples, endpoint=False)
    audio = 0.08 * np.sign(np.sin(2 * np.pi * 800 * t))  # square wave
    audio *= _adsr(num_samples, attack=0.001, release=0.02)
    return _to_wav_bytes(audio)


def generate_correct_wav() -> bytes:
    """Tono ascendente alegre: Re5 → Sol5."""
    sr = SAMPLE_RATE
    seg1 = 0.12
    seg2 = 0.18
    n1 = int(seg1 * sr)
    n2 = int(seg2 * sr)
    pause = int(0.02 * sr)
    t1 = np.linspace(0, seg1, n1, endpoint=False)
    t2 = np.linspace(0, seg2, n2, endpoint=False)
    note1 = 0.45 * np.sin(2 * np.pi * 587.33 * t1) * _adsr(n1, 0.005, 0.05)
    note2 = 0.45 * np.sin(2 * np.pi * 783.99 * t2) * _adsr(n2, 0.005, 0.08)
    audio = np.concatenate([note1, np.zeros(pause), note2])
    return _to_wav_bytes(audio)


def generate_wrong_wav() -> bytes:
    """Buzzer grave de error."""
    sr = SAMPLE_RATE
    duration = 0.35
    n = int(duration * sr)
    t = np.linspace(0, duration, n, endpoint=False)
    # Dos tonos sawtooth descendentes
    audio = 0.35 * _sawtooth(200, t)
    audio += 0.35 * _sawtooth(150, t)
    audio *= _adsr(n, 0.005, 0.15)
    return _to_wav_bytes(audio)


def generate_win_wav() -> bytes:
    """Arpegio mayor ascendente: Do-Mi-Sol-Do."""
    sr = SAMPLE_RATE
    note_dur = 0.22
    n = int(note_dur * sr)
    t_note = np.linspace(0, note_dur, n, endpoint=False)

    notes_freq = [523.25, 659.25, 783.99, 1046.50]
    audio = np.zeros(0)
    for f in notes_freq:
        # Onda triangular para sonido más cálido
        wave = np.arcsin(np.sin(2 * np.pi * f * t_note)) * (2 / np.pi)
        wave *= 0.5 * _adsr(n, 0.01, 0.1)
        audio = np.concatenate([audio, wave])
    return _to_wav_bytes(audio)


def generate_lose_wav() -> bytes:
    """Descenso cromático triste: Sol-Fa#-Fa-Mib."""
    sr = SAMPLE_RATE
    note_dur = 0.3
    n = int(note_dur * sr)
    t_note = np.linspace(0, note_dur, n, endpoint=False)

    notes_freq = [392.00, 369.99, 349.23, 311.13]
    audio = np.zeros(0)
    for f in notes_freq:
        wave = 0.45 * np.sin(2 * np.pi * f * t_note)
        wave *= _adsr(n, 0.01, 0.15)
        audio = np.concatenate([audio, wave])
    return _to_wav_bytes(audio)


if __name__ == "__main__":
    # Pruebas: genera todos los archivos a disco para inspeccionarlos
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    files = {
        "test_bg_tension.wav": generate_bg_tension_wav(),
        "test_click.wav": generate_click_wav(),
        "test_correct.wav": generate_correct_wav(),
        "test_wrong.wav": generate_wrong_wav(),
        "test_win.wav": generate_win_wav(),
        "test_lose.wav": generate_lose_wav(),
    }
    for fname, data in files.items():
        path = os.path.join(out_dir, fname)
        with open(path, "wb") as f:
            f.write(data)
        print(f"  {fname}: {len(data):>9} bytes")
    print("Generación OK.")
