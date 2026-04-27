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
# MÚSICA DE FONDO: LATIDO CARDÍACO + RESPIRACIÓN AGITADA
# ============================================================
def _add_heart_thump(audio: np.ndarray, t_start: float,
                     freq_start: float, freq_end: float,
                     volume: float, duration_s: float,
                     decay_tau: float, sample_rate: int = SAMPLE_RATE) -> None:
    """
    Añade un golpe de corazón al array `audio` in-place.
    Modela un kick drum: barrido exponencial de freq_start a freq_end,
    con envolvente de ataque inmediato y decay exponencial.
    """
    n = int(duration_s * sample_rate)
    start_idx = int(t_start * sample_rate)
    end_idx = min(start_idx + n, len(audio))
    n = end_idx - start_idx
    if n <= 0:
        return
    tt = np.linspace(0, duration_s, n)
    freq_curve = freq_end + (freq_start - freq_end) * np.exp(-tt / 0.03)
    phase = 2 * np.pi * np.cumsum(freq_curve) / sample_rate
    wave = np.sin(phase)
    attack_samples = int(0.003 * sample_rate)
    envelope = np.ones(n)
    if 0 < attack_samples < n:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    envelope *= np.exp(-tt / decay_tau)
    audio[start_idx:end_idx] += volume * wave * envelope


def _add_breath(audio: np.ndarray, t_start: float, kind: str,
                volume: float = 0.35, sample_rate: int = SAMPLE_RATE) -> None:
    """
    Añade un ciclo de respiración (inhale o exhale) al array `audio` in-place.
    - inhale: aire sibilante agudo, corto y áspero (~0.35s)
    - exhale: aire grave exhalado, más largo y suave (~0.70s)
    Sintetizado con ruido blanco filtrado + envolvente.
    """
    if kind == 'inhale':
        duration_s = 0.35
        attack_s, release_s = 0.10, 0.25  # rampa arriba rápida, baja moderada
    else:  # exhale
        duration_s = 0.70
        attack_s, release_s = 0.20, 0.50  # rampa más lenta y larga

    n = int(duration_s * sample_rate)
    start_idx = int(t_start * sample_rate)
    end_idx = min(start_idx + n, len(audio))
    n = end_idx - start_idx
    if n <= 0:
        return

    # Ruido blanco con seed determinística (cache estable entre runs)
    rng = np.random.default_rng(seed=int(t_start * 1000) % 2**32)
    noise = rng.standard_normal(n) * 0.5

    # Filtrado por tipo (banda de frecuencia distinta para inhale vs exhale)
    if kind == 'inhale':
        # Quitar graves para que sea sibilante: noise - lowpass(noise, muy bajo)
        low_freqs = _lowpass_simple(noise, 0.05)
        noise = noise - low_freqs
        # Suavizar agudos extremos
        noise = _lowpass_simple(noise, 0.55)
    else:  # exhale
        # Lowpass agresivo: dominan los graves, tipo "ahhhh" exhausto
        noise = _lowpass_simple(noise, 0.25)

    # Envolvente triangular asimétrica (forma de respiración)
    a = int(attack_s * sample_rate)
    r = int(release_s * sample_rate)
    a = min(a, n // 2)
    r = min(r, n - a)
    envelope = np.zeros(n)
    if a > 0:
        envelope[:a] = np.linspace(0, 1, a)
    if r > 0:
        envelope[a:a + r] = np.linspace(1, 0, r)

    audio[start_idx:end_idx] += volume * noise * envelope


def generate_bg_tension_wav(bpm: int = 90, breath_per_min: int = 40,
                            duration: float = 12.0) -> bytes:
    """
    Loop de fondo: latido cardíaco fuerte + respiración agitada (jadeo).
    
    Por defecto:
      - Corazón a 90 BPM (ansiedad palpable)
      - Respiración a 40/min (jadeo agitado)
      - Duración: 12s = 18 latidos + 8 respiraciones = loop perfecto
    """
    sr = SAMPLE_RATE
    num_samples = int(duration * sr)

    # ----- ARRAY 1: LATIDOS DEL CORAZÓN (fuerte) -----
    heart = np.zeros(num_samples)
    beat_interval = 60.0 / bpm
    beat_count = int(np.floor(duration / beat_interval))
    for k in range(beat_count):
        t_lub = k * beat_interval
        # LUB (S1): grave fuerte
        _add_heart_thump(
            heart, t_lub,
            freq_start=110, freq_end=22,
            volume=2.30, duration_s=0.16,
            decay_tau=0.045,
        )
        # DUB (S2): un poco más agudo y corto, 135 ms después
        t_dub = t_lub + 0.135
        _add_heart_thump(
            heart, t_dub,
            freq_start=90, freq_end=30,
            volume=1.35, duration_s=0.12,
            decay_tau=0.032,
        )

    # Sub-bass continuo (presión en el pecho)
    t_full = np.arange(num_samples) / sr
    sub_bass = 0.09 * np.sin(2 * np.pi * 32 * t_full)
    heart = heart + sub_bass

    # Filtro pasa-bajos AL CORAZÓN solamente (deja respiración intacta)
    heart = _lowpass_simple(heart, 0.30)

    # ----- ARRAY 2: RESPIRACIÓN AGITADA (jadeo) -----
    breath = np.zeros(num_samples)
    breath_interval = 60.0 / breath_per_min  # 1.5s a 40/min
    breath_count = int(np.floor(duration / breath_interval))
    for k in range(breath_count):
        t_inhale = k * breath_interval
        _add_breath(breath, t_inhale, kind='inhale', volume=0.10)
        t_exhale = t_inhale + 0.45  # 100ms después de que termine el inhale
        _add_breath(breath, t_exhale, kind='exhale', volume=0.08)

    # ----- MEZCLA FINAL -----
    audio = heart + breath

    # Crossfade en los extremos para loop perfecto
    fade_samples = int(0.04 * sr)
    if fade_samples > 0:
        audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

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
