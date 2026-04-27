import io
import re
import base64
import streamlit as st
import streamlit.components.v1 as components
from docx import Document
from audio_gen import (
    generate_bg_tension_wav,
    generate_click_wav,
    generate_correct_wav,
    generate_wrong_wav,
    generate_win_wav,
    generate_lose_wav,
)

# --- Constantes ---
MAX_WRONG_GUESSES = 6
INVALID_CHARS_RE = re.compile(r'[^A-ZÁÉÍÓÚÜÑ]')
ALPHABET = 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'
ALL_LETTERS = ALPHABET
AUTO_REVEAL = {' ', 'Á', 'É', 'Í', 'Ó', 'Ú', 'Ü'}  # se muestran sin adivinar


# ============================================================
# AUDIO: generación una sola vez con cache
# ============================================================
@st.cache_data(show_spinner=False)
def _bg_tension_wav() -> bytes:
    return generate_bg_tension_wav()

@st.cache_data(show_spinner=False)
def _correct_wav() -> bytes:
    return generate_correct_wav()

@st.cache_data(show_spinner=False)
def _wrong_wav() -> bytes:
    return generate_wrong_wav()

@st.cache_data(show_spinner=False)
def _win_wav() -> bytes:
    return generate_win_wav()

@st.cache_data(show_spinner=False)
def _lose_wav() -> bytes:
    return generate_lose_wav()


def play_effect(sound_name: str):
    """Inyecta un <audio autoplay> invisible para reproducir un efecto puntual."""
    sounds = {
        'correct': _correct_wav,
        'wrong':   _wrong_wav,
        'win':     _win_wav,
        'lose':    _lose_wav,
    }
    if sound_name not in sounds:
        return
    wav_bytes = sounds[sound_name]()
    b64 = base64.b64encode(wav_bytes).decode('ascii')
    components.html(
        f'<audio autoplay style="display:none">'
        f'<source src="data:audio/wav;base64,{b64}" type="audio/wav">'
        f'</audio>',
        height=0,
    )


def render_bg_music():
    """Reproductor de música de fondo en loop. Se renderiza una vez por rerun."""
    wav_bytes = _bg_tension_wav()
    with st.expander("💓 Corazón + respiración agitada", expanded=False):
        st.caption(
            "Latido a 90 BPM + jadeo a 40 resp/min en loop infinito. "
            "Si no se reproduce, presiona ▶ una vez (autoplay del navegador)."
        )
        st.audio(wav_bytes, format="audio/wav", loop=True, autoplay=True)


# ============================================================
# SVG / ANIMACIONES (sin cambios respecto a la versión original)
# ============================================================
def get_hangman_svg(wrong_guesses: int) -> str:
    def vis(show: bool) -> str:
        return 'visible' if show else 'hidden'
    return f"""
    <svg height="300" width="240" viewBox="0 0 240 300" xmlns="http://www.w3.org/2000/svg">
      <line x1="10" y1="280" x2="230" y2="280" stroke="#374151" stroke-width="5" stroke-linecap="round"/>
      <path d="M 168 48 Q 142 0, 185 6 Q 222 12, 210 48 Q 222 74, 185 80 Q 148 74, 168 48 Z"
            fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
      <path d="M 58 95 Q 30 58, 68 44 Q 108 32, 120 60 Q 132 95, 96 107 Q 58 118, 58 95 Z"
            fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
      <path d="M 148 22 Q 130 -5, 162 2 Q 188 8, 180 28 Q 186 46, 162 50 Q 136 46, 148 22 Z"
            fill="#3a9b5c" stroke="#228B22" stroke-width="1"/>
      <path d="M 94 280 C 80 215, 104 172, 92 56"
            stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
      <path d="M 92 98 C 66 84, 52 70, 50 44"
            stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
      <path d="M 92 270 C 70 265, 50 268, 38 278"
            stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>
      <path d="M 96 270 C 116 265, 136 268, 148 278"
            stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>
      <path d="M 92 58 Q 106 24, 185 24"
            stroke="#4B3621" stroke-width="5" fill="none" stroke-linecap="round"/>
      <line x1="185" y1="24" x2="185" y2="58"
            stroke="#4B3621" stroke-width="5" stroke-linecap="round"/>
      <ellipse cx="185" cy="60" rx="5" ry="3"
               stroke="#5c4a32" stroke-width="2" fill="#7a6244"
               visibility="{vis(wrong_guesses >= 1)}"/>
      <circle cx="185" cy="80" r="22" stroke="#374151" stroke-width="4" fill="#f5e6d3"
              visibility="{vis(wrong_guesses >= 1)}"/>
      <circle cx="178" cy="76" r="3" fill="#374151"
              visibility="{vis(wrong_guesses >= 1)}"/>
      <circle cx="192" cy="76" r="3" fill="#374151"
              visibility="{vis(wrong_guesses >= 1)}"/>
      <path d="M 178 89 Q 185 84, 192 89"
            stroke="#374151" stroke-width="2" fill="none" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 1)}"/>
      <line x1="185" y1="102" x2="185" y2="168"
            stroke="#374151" stroke-width="5" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 2)}"/>
      <line x1="185" y1="122" x2="150" y2="148"
            stroke="#374151" stroke-width="4" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 3)}"/>
      <circle cx="148" cy="150" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"
              visibility="{vis(wrong_guesses >= 3)}"/>
      <line x1="185" y1="122" x2="220" y2="148"
            stroke="#374151" stroke-width="4" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 4)}"/>
      <circle cx="222" cy="150" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"
              visibility="{vis(wrong_guesses >= 4)}"/>
      <line x1="185" y1="168" x2="155" y2="205"
            stroke="#374151" stroke-width="4" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 5)}"/>
      <line x1="155" y1="205" x2="140" y2="208"
            stroke="#374151" stroke-width="3" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 5)}"/>
      <line x1="185" y1="168" x2="215" y2="205"
            stroke="#374151" stroke-width="4" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 6)}"/>
      <line x1="215" y1="205" x2="230" y2="208"
            stroke="#374151" stroke-width="3" stroke-linecap="round"
            visibility="{vis(wrong_guesses >= 6)}"/>
    </svg>
    """


def get_win_animation_html() -> str:
    return """<!DOCTYPE html>
<html><head>
<style>html,body{margin:0;padding:0;background:transparent;display:flex;justify-content:center;overflow:hidden;}</style>
</head><body>
<svg height="300" width="240" viewBox="0 0 240 300" xmlns="http://www.w3.org/2000/svg" overflow="visible">
  <line x1="10" y1="280" x2="270" y2="280" stroke="#374151" stroke-width="5" stroke-linecap="round"/>
  <path d="M 168 48 Q 142 0, 185 6 Q 222 12, 210 48 Q 222 74, 185 80 Q 148 74, 168 48 Z"
        fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
  <path d="M 58 95 Q 30 58, 68 44 Q 108 32, 120 60 Q 132 95, 96 107 Q 58 118, 58 95 Z"
        fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
  <path d="M 148 22 Q 130 -5, 162 2 Q 188 8, 180 28 Q 186 46, 162 50 Q 136 46, 148 22 Z"
        fill="#3a9b5c" stroke="#228B22" stroke-width="1"/>
  <path d="M 94 280 C 80 215, 104 172, 92 56"
        stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
  <path d="M 92 98 C 66 84, 52 70, 50 44"
        stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
  <path d="M 92 270 C 70 265, 50 268, 38 278"
        stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>
  <path d="M 96 270 C 116 265, 136 268, 148 278"
        stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>
  <path d="M 92 58 Q 106 24, 185 24"
        stroke="#4B3621" stroke-width="5" fill="none" stroke-linecap="round"/>
  <line x1="185" y1="24" x2="185" y2="58" stroke="#4B3621" stroke-width="5" stroke-linecap="round"/>
  <ellipse cx="185" cy="62" rx="5" ry="4" stroke="#5c4a32" stroke-width="2" fill="#7a6244"/>
  <g id="fig" transform="translate(185,80)">
    <g id="lgL">
      <line x1="0" y1="88" x2="-30" y2="125" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <line x1="-30" y1="125" x2="-45" y2="128" stroke="#374151" stroke-width="3" stroke-linecap="round"/>
    </g>
    <g id="lgR">
      <line x1="0" y1="88" x2="30" y2="125" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <line x1="30" y1="125" x2="45" y2="128" stroke="#374151" stroke-width="3" stroke-linecap="round"/>
    </g>
    <g id="arL">
      <line x1="0" y1="42" x2="-35" y2="68" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <circle cx="-37" cy="70" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"/>
    </g>
    <g id="arR">
      <line x1="0" y1="42" x2="35" y2="68" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <circle cx="37" cy="70" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"/>
    </g>
    <line x1="0" y1="22" x2="0" y2="88" stroke="#374151" stroke-width="5" stroke-linecap="round"/>
    <circle cx="0" cy="0" r="22" stroke="#374151" stroke-width="4" fill="#f5e6d3"/>
    <circle cx="-7" cy="-4" r="3" fill="#374151"/>
    <circle cx="7" cy="-4" r="3" fill="#374151"/>
    <path id="mouth" d="M -7 9 Q 0 4, 7 9"
          stroke="#374151" stroke-width="2" fill="none" stroke-linecap="round"/>
  </g>
</svg>
<script>
(function(){
  var fig=document.getElementById('fig'),
      mouth=document.getElementById('mouth'),
      lgL=document.getElementById('lgL'), lgR=document.getElementById('lgR'),
      arL=document.getElementById('arL'), arR=document.getElementById('arR');
  var FALL_END=700, STAND_END=1200, REPO_END=1550, WALK_END=4200;
  var HX=185, HY=80, SY=152, WALK_X0=22, WALK_X1=265;
  var happy=false, t0=null;
  function easeOut(t){ return 1-Math.pow(1-t,3); }
  function easeIO(t){ return t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2; }
  function setT(x,y,r){
    fig.setAttribute('transform','translate('+x+','+y+') rotate('+r+')');
  }
  function setHappy(){
    if(!happy){ mouth.setAttribute('d','M -8 6 Q 0 14, 8 6'); happy=true; }
  }
  function resetLimbs(){
    lgL.removeAttribute('transform'); lgR.removeAttribute('transform');
    arL.removeAttribute('transform'); arR.removeAttribute('transform');
  }
  function applyWalk(e){
    var a=Math.sin((e-REPO_END)/350*Math.PI*2)*28;
    lgL.setAttribute('transform','rotate('+a+',0,88)');
    lgR.setAttribute('transform','rotate('+(-a)+',0,88)');
    arL.setAttribute('transform','rotate('+(-a*0.5)+',0,42)');
    arR.setAttribute('transform','rotate('+(a*0.5)+',0,42)');
  }
  function frame(ts){
    if(!t0) t0=ts;
    var e=ts-t0;
    if(e<FALL_END){
      var t=easeOut(e/FALL_END);
      setT(HX, HY+t*(SY-HY), Math.sin(t*Math.PI)*10);
      resetLimbs();
    } else if(e<STAND_END){
      var t=easeIO((e-FALL_END)/(STAND_END-FALL_END));
      setT(HX, SY, (1-t)*10);
      resetLimbs();
      if(t>0.6) setHappy();
    } else if(e<REPO_END){
      var t=easeIO((e-STAND_END)/(REPO_END-STAND_END));
      setT(HX+t*(WALK_X0-HX), SY, 0);
      setHappy();
      resetLimbs();
    } else if(e<WALK_END){
      var t=(e-REPO_END)/(WALK_END-REPO_END);
      setT(WALK_X0+t*(WALK_X1-WALK_X0), SY, 0);
      setHappy();
      applyWalk(e);
    }
    if(e<WALK_END) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
</body></html>"""


def get_lose_animation_html() -> str:
    return """<!DOCTYPE html>
<html><head>
<style>html,body{margin:0;padding:0;background:transparent;display:flex;justify-content:center;overflow:hidden;}</style>
</head><body>
<svg height="300" width="240" viewBox="0 0 240 300" xmlns="http://www.w3.org/2000/svg">
  <line x1="10" y1="280" x2="230" y2="280" stroke="#374151" stroke-width="5" stroke-linecap="round"/>
  <path d="M 168 48 Q 142 0, 185 6 Q 222 12, 210 48 Q 222 74, 185 80 Q 148 74, 168 48 Z"
        fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
  <path d="M 58 95 Q 30 58, 68 44 Q 108 32, 120 60 Q 132 95, 96 107 Q 58 118, 58 95 Z"
        fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
  <path d="M 148 22 Q 130 -5, 162 2 Q 188 8, 180 28 Q 186 46, 162 50 Q 136 46, 148 22 Z"
        fill="#3a9b5c" stroke="#228B22" stroke-width="1"/>
  <path d="M 94 280 C 80 215, 104 172, 92 56"
        stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
  <path d="M 92 98 C 66 84, 52 70, 50 44"
        stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
  <path d="M 92 270 C 70 265, 50 268, 38 278"
        stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>
  <path d="M 96 270 C 116 265, 136 268, 148 278"
        stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>
  <path d="M 92 58 Q 106 24, 185 24"
        stroke="#4B3621" stroke-width="5" fill="none" stroke-linecap="round"/>
  <line x1="185" y1="24" x2="185" y2="58" stroke="#4B3621" stroke-width="5" stroke-linecap="round"/>
  <ellipse cx="185" cy="62" rx="5" ry="4" stroke="#5c4a32" stroke-width="2" fill="#7a6244"/>
  <g id="dust" opacity="0">
    <ellipse cx="85" cy="273" rx="50" ry="11" fill="#a07850" opacity="0.55"/>
    <ellipse cx="60" cy="266" rx="14" ry="10" fill="#a07850" opacity="0.4"/>
    <ellipse cx="118" cy="267" rx="11" ry="8" fill="#a07850" opacity="0.35"/>
  </g>
  <g id="stars" opacity="0">
    <text x="1" y="240" font-size="13" fill="#fbbf24">✦</text>
    <text x="38" y="236" font-size="11" fill="#f87171">✦</text>
    <text x="-2" y="272" font-size="10" fill="#fbbf24">✦</text>
  </g>
  <g id="tears" opacity="0">
    <ellipse id="tr1" cx="21" cy="248" rx="2.5" ry="3.5" fill="#60a5fa"/>
    <ellipse id="tr2" cx="21" cy="263" rx="2.5" ry="3.5" fill="#93c5fd"/>
    <ellipse id="tr3" cx="16" cy="255" rx="2" ry="3" fill="#60a5fa"/>
  </g>
  <g id="fig" transform="translate(185,80)">
    <g id="lgL">
      <line x1="0" y1="88" x2="-30" y2="125" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <line x1="-30" y1="125" x2="-45" y2="128" stroke="#374151" stroke-width="3" stroke-linecap="round"/>
    </g>
    <g id="lgR">
      <line x1="0" y1="88" x2="30" y2="125" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <line x1="30" y1="125" x2="45" y2="128" stroke="#374151" stroke-width="3" stroke-linecap="round"/>
    </g>
    <g id="arL">
      <line x1="0" y1="42" x2="-35" y2="68" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <circle cx="-37" cy="70" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"/>
    </g>
    <g id="arR">
      <line x1="0" y1="42" x2="35" y2="68" stroke="#374151" stroke-width="4" stroke-linecap="round"/>
      <circle cx="37" cy="70" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"/>
    </g>
    <line x1="0" y1="22" x2="0" y2="88" stroke="#374151" stroke-width="5" stroke-linecap="round"/>
    <circle cx="0" cy="0" r="22" stroke="#374151" stroke-width="4" fill="#f5e6d3"/>
    <circle id="ey-l" cx="-7" cy="-4" r="3" fill="#374151"/>
    <circle id="ey-r" cx="7" cy="-4" r="3" fill="#374151"/>
    <g id="xe-l" visibility="hidden">
      <line x1="-11" y1="-8" x2="-3" y2="0" stroke="#374151" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="-3" y1="-8" x2="-11" y2="0" stroke="#374151" stroke-width="2.5" stroke-linecap="round"/>
    </g>
    <g id="xe-r" visibility="hidden">
      <line x1="3" y1="-8" x2="11" y2="0" stroke="#374151" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="11" y1="-8" x2="3" y2="0" stroke="#374151" stroke-width="2.5" stroke-linecap="round"/>
    </g>
    <path id="mth" d="M -7 9 Q 0 4, 7 9"
          stroke="#374151" stroke-width="2" fill="none" stroke-linecap="round"/>
  </g>
</svg>
<script>
(function(){
  var fig=document.getElementById('fig');
  var eyL=document.getElementById('ey-l'), eyR=document.getElementById('ey-r');
  var xeL=document.getElementById('xe-l'), xeR=document.getElementById('xe-r');
  var dust=document.getElementById('dust');
  var stars=document.getElementById('stars');
  var tears=document.getElementById('tears');
  var tr1=document.getElementById('tr1'),tr2=document.getElementById('tr2'),tr3=document.getElementById('tr3');
  var FALL_END=1100, IMPACT_END=1450, TOTAL=7000;
  var HX=185, HY=80, DX=25, DY=255;
  var t0=null, dead=false;
  function easeOut(t){ return 1-Math.pow(1-t,3); }
  function makeDead(){
    if(!dead){
      fig.setAttribute('transform','translate('+DX+','+DY+') rotate(90)');
      eyL.setAttribute('visibility','hidden');
      eyR.setAttribute('visibility','hidden');
      xeL.setAttribute('visibility','visible');
      xeR.setAttribute('visibility','visible');
      dead=true;
    }
  }
  function animTears(e){
    var cyc=1800;
    function drop(base, offset){
      var t=((e-IMPACT_END+offset)%cyc)/cyc;
      return {y: base+t*24, op: t<0.78?1:(1-t)/0.22};
    }
    var a=drop(248,0); tr1.setAttribute('cy',a.y); tr1.setAttribute('opacity',a.op);
    var b=drop(263,620); tr2.setAttribute('cy',b.y); tr2.setAttribute('opacity',b.op);
    var c=drop(255,1240); tr3.setAttribute('cy',c.y); tr3.setAttribute('opacity',c.op);
  }
  function frame(ts){
    if(!t0) t0=ts;
    var e=ts-t0;
    if(e<FALL_END){
      var t=easeOut(e/FALL_END);
      fig.setAttribute('transform',
        'translate('+HX+','+(HY+t*(DY-HY))+') rotate('+(t*720)+')');
    } else if(e<IMPACT_END){
      var t=(e-FALL_END)/(IMPACT_END-FALL_END);
      makeDead();
      dust.setAttribute('opacity', t<0.4?t/0.4:1-(t-0.4)/0.6);
      stars.setAttribute('opacity', t>0.5?(t-0.5)/0.5:0);
      tears.setAttribute('opacity', t>0.6?(t-0.6)/0.4:0);
    } else {
      makeDead();
      dust.setAttribute('opacity',0);
      stars.setAttribute('opacity',1);
      tears.setAttribute('opacity',1);
      animTears(e);
    }
    if(e<TOTAL) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
</body></html>"""


# ============================================================
# LÓGICA DEL JUEGO
# ============================================================
def extract_words_from_docx(file_bytes: bytes) -> list:
    doc = Document(io.BytesIO(file_bytes))
    phrases = []
    for para in doc.paragraphs:
        line = para.text.upper().strip()
        cleaned = re.sub(r'[^A-ZÁÉÍÓÚÜÑ ]', '', line)
        cleaned = re.sub(r' {2,}', ' ', cleaned).strip()
        if len(cleaned.replace(' ', '')) > 2:
            phrases.append(cleaned)
    return phrases


def init_state():
    defaults = {
        'phase': 'upload',
        'word_list': [],
        'selected_word': '',
        'correct_letters': set(),
        'wrong_guesses': 0,
        'is_game_over': False,
        'is_win': False,
        'guessed_letters': set(),
        'pending_sound': None,  # 'correct' | 'wrong' | 'win' | 'lose' | None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_game():
    st.session_state.correct_letters = set()
    st.session_state.wrong_guesses = 0
    st.session_state.is_game_over = False
    st.session_state.is_win = False
    st.session_state.guessed_letters = set()
    st.session_state.pending_sound = None


def handle_guess(letter: str):
    if st.session_state.is_game_over or letter in st.session_state.guessed_letters:
        return
    st.session_state.guessed_letters.add(letter)
    if letter in st.session_state.selected_word:
        st.session_state.correct_letters.add(letter)
        st.session_state.pending_sound = 'correct'
        if all(l in st.session_state.correct_letters
               for l in st.session_state.selected_word
               if l not in AUTO_REVEAL):
            st.session_state.is_game_over = True
            st.session_state.is_win = True
            st.session_state.pending_sound = 'win'
    else:
        st.session_state.wrong_guesses += 1
        st.session_state.pending_sound = 'wrong'
        if st.session_state.wrong_guesses >= MAX_WRONG_GUESSES:
            st.session_state.is_game_over = True
            st.session_state.is_win = False
            st.session_state.pending_sound = 'lose'


def render_word():
    word = st.session_state.selected_word
    correct = st.session_state.correct_letters
    is_game_over = st.session_state.is_game_over
    is_win = st.session_state.is_win
    word_groups = word.split(' ')
    group_htmls = []
    for group in word_groups:
        letter_spans = []
        for letter in group:
            auto = letter in AUTO_REVEAL
            revealed = auto or letter in correct
            show_red = is_game_over and not is_win and not revealed
            if revealed:
                border_color, text, color = '#9ca3af', letter, '#1f2937'
            elif show_red:
                border_color, text, color = '#f87171', letter, '#ef4444'
            else:
                border_color, text, color = '#9ca3af', '&nbsp;', 'transparent'
            letter_spans.append(
                f'<span style="display:inline-block;border-bottom:4px solid {border_color};'
                f'margin:4px 6px;min-width:2rem;height:2.8rem;text-align:center;'
                f'font-size:2rem;font-family:monospace;color:{color};font-weight:bold;'
                f'line-height:2.8rem">{text}</span>'
            )
        group_htmls.append(
            f'<span style="display:inline-block;white-space:nowrap">{"".join(letter_spans)}</span>'
        )
    separator = '<span style="display:inline-block;min-width:1.2rem;height:2.8rem;margin:4px 0"></span>'
    st.markdown(
        f'<div style="text-align:center;min-height:4rem;margin:1.5rem 0;'
        f'display:flex;flex-wrap:wrap;justify-content:center;align-items:flex-end;gap:0">'
        f'{separator.join(group_htmls)}</div>',
        unsafe_allow_html=True,
    )


def render_keyboard():
    guessed = st.session_state.guessed_letters
    correct = st.session_state.correct_letters
    letters = list(ALL_LETTERS)
    rows = [letters[i:i + 9] for i in range(0, len(letters), 9)]
    for row in rows:
        cols = st.columns(len(row))
        for i, letter in enumerate(row):
            with cols[i]:
                if letter in guessed:
                    color = '#4ade80' if letter in correct else '#f87171'
                    st.markdown(
                        f'<div style="background:{color};color:white;border-radius:8px;'
                        f'text-align:center;padding:9px 0;font-weight:bold;font-size:1rem;'
                        f'margin:2px;cursor:default">{letter}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(letter, key=f"key_{letter}"):
                        handle_guess(letter)
                        st.rerun()


def main():
    st.set_page_config(page_title="Juego del Ahorcado", page_icon="🎮", layout="centered")
    st.markdown("""
    <style>
    .stButton > button { width: 100%; font-weight: bold; font-size: 1rem; }
    h1 { text-align: center; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

    init_state()
    st.title("Juego del Ahorcado")

    # --- FASE: CARGA DE ARCHIVO ---
    if st.session_state.phase == 'upload':
        st.write("Sube un archivo de Word (.docx) con una lista de palabras para empezar a jugar.")
        uploaded_file = st.file_uploader("Selecciona un archivo .docx", type=['docx'])
        if uploaded_file is not None:
            words = extract_words_from_docx(uploaded_file.read())
            if not words:
                st.error("No se encontraron palabras válidas en el archivo.")
            else:
                st.session_state.word_list = words
                st.session_state.phase = 'select'
                st.rerun()

    # --- FASE: SELECCIÓN DE PALABRA ---
    elif st.session_state.phase == 'select':
        word_count = len(st.session_state.word_list)
        st.info(f"Se encontraron **{word_count}** palabras. Ingresa un número entre 1 y {word_count}.")
        word_num = st.number_input("Número de palabra", min_value=1, max_value=word_count, step=1, value=1)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶ Empezar Juego", type="primary", use_container_width=True):
                st.session_state.selected_word = st.session_state.word_list[int(word_num) - 1]
                reset_game()
                st.session_state.phase = 'game'
                st.rerun()
        with col2:
            if st.button("✖ Cancelar", use_container_width=True):
                st.session_state.phase = 'upload'
                st.session_state.word_list = []
                st.rerun()

    # --- FASE: JUEGO ---
    elif st.session_state.phase == 'game':
        # 🎵 MÚSICA DE FONDO (en loop, siempre visible durante el juego)
        render_bg_music()

        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            if st.session_state.is_win:
                components.html(get_win_animation_html(), height=320, scrolling=False)
            elif st.session_state.is_game_over:
                components.html(get_lose_animation_html(), height=320, scrolling=False)
            else:
                html = (
                    "<!DOCTYPE html><html>"
                    "<head><style>html,body{margin:0;padding:0;background:transparent;"
                    "display:flex;justify-content:center;}</style></head>"
                    f"<body>{get_hangman_svg(st.session_state.wrong_guesses)}</body>"
                    "</html>"
                )
                components.html(html, height=320, scrolling=False)

        st.markdown(
            f'<p style="text-align:center;color:#6b7280;margin-top:-0.5rem">'
            f'Errores: {st.session_state.wrong_guesses} / {MAX_WRONG_GUESSES}</p>',
            unsafe_allow_html=True,
        )
        render_word()

        if st.session_state.is_game_over:
            if st.session_state.is_win:
                st.success("🎉 ¡Felicidades, ganaste! 🎉")
            else:
                st.error(f"😕 ¡Perdiste! La palabra era: **{st.session_state.selected_word}**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Jugar de Nuevo", type="primary", use_container_width=True):
                    st.session_state.phase = 'select'
                    st.rerun()
            with col2:
                if st.button("📂 Nuevo Archivo", use_container_width=True):
                    st.session_state.phase = 'upload'
                    st.session_state.word_list = []
                    st.rerun()
        else:
            render_keyboard()

        # 🔊 EFECTO PUNTUAL (correct/wrong/win/lose) - se inyecta al final del render
        if st.session_state.pending_sound:
            play_effect(st.session_state.pending_sound)
            st.session_state.pending_sound = None


if __name__ == "__main__":
    main()
