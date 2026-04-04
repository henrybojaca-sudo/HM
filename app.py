import io
import re

import streamlit as st
import streamlit.components.v1 as components
from docx import Document

# --- Constantes ---
MAX_WRONG_GUESSES = 6
INVALID_CHARS_RE = re.compile(r'[^A-ZÁÉÍÓÚÜÑ]')
ALPHABET = 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'
ACCENTED_VOWELS = 'ÁÉÍÓÚÜ'
ALL_LETTERS = ALPHABET + ACCENTED_VOWELS


def get_hangman_svg(wrong_guesses: int) -> str:
    def vis(show: bool) -> str:
        return 'visible' if show else 'hidden'

    return f"""
    <svg height="300" width="240" viewBox="0 0 240 300" xmlns="http://www.w3.org/2000/svg">
        <!-- Suelo -->
        <line x1="10" y1="280" x2="230" y2="280" stroke="#374151" stroke-width="5" stroke-linecap="round"/>

        <!-- Follaje derecho del árbol -->
        <path d="M 168 48 Q 142 0, 185 6 Q 222 12, 210 48 Q 222 74, 185 80 Q 148 74, 168 48 Z"
              fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
        <!-- Follaje izquierdo del árbol -->
        <path d="M 58 95 Q 30 58, 68 44 Q 108 32, 120 60 Q 132 95, 96 107 Q 58 118, 58 95 Z"
              fill="#2E8B57" stroke="#228B22" stroke-width="1.5"/>
        <!-- Follaje pequeño derecho -->
        <path d="M 148 22 Q 130 -5, 162 2 Q 188 8, 180 28 Q 186 46, 162 50 Q 136 46, 148 22 Z"
              fill="#3a9b5c" stroke="#228B22" stroke-width="1"/>

        <!-- Tronco principal -->
        <path d="M 94 280 C 80 215, 104 172, 92 56"
              stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
        <!-- Rama lateral izquierda -->
        <path d="M 92 98 C 66 84, 52 70, 50 44"
              stroke="#8B4513" stroke-width="10" fill="none" stroke-linecap="round"/>
        <!-- Raíz izquierda -->
        <path d="M 92 270 C 70 265, 50 268, 38 278"
              stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>
        <!-- Raíz derecha -->
        <path d="M 96 270 C 116 265, 136 268, 148 278"
              stroke="#6B3410" stroke-width="6" fill="none" stroke-linecap="round"/>

        <!-- Viga horizontal de la horca -->
        <path d="M 92 58 Q 106 24, 185 24"
              stroke="#4B3621" stroke-width="5" fill="none" stroke-linecap="round"/>
        <!-- Cuerda vertical -->
        <line x1="185" y1="24" x2="185" y2="58"
              stroke="#4B3621" stroke-width="5" stroke-linecap="round"/>

        <!-- Nudo de la soga -->
        <ellipse cx="185" cy="60" rx="5" ry="3"
                 stroke="#5c4a32" stroke-width="2" fill="#7a6244"
                 visibility="{vis(wrong_guesses >= 1)}"/>

        <!-- Cabeza con cara -->
        <circle cx="185" cy="80" r="22" stroke="#374151" stroke-width="4" fill="#f5e6d3"
                visibility="{vis(wrong_guesses >= 1)}"/>
        <!-- Ojos (tristes al perder) -->
        <circle cx="178" cy="76" r="3" fill="#374151"
                visibility="{vis(wrong_guesses >= 1)}"/>
        <circle cx="192" cy="76" r="3" fill="#374151"
                visibility="{vis(wrong_guesses >= 1)}"/>
        <!-- Boca triste -->
        <path d="M 178 89 Q 185 84, 192 89"
              stroke="#374151" stroke-width="2" fill="none" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 1)}"/>

        <!-- Cuerpo -->
        <line x1="185" y1="102" x2="185" y2="168"
              stroke="#374151" stroke-width="5" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 2)}"/>

        <!-- Brazo izquierdo -->
        <line x1="185" y1="122" x2="150" y2="148"
              stroke="#374151" stroke-width="4" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 3)}"/>
        <!-- Mano izquierda -->
        <circle cx="148" cy="150" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"
                visibility="{vis(wrong_guesses >= 3)}"/>

        <!-- Brazo derecho -->
        <line x1="185" y1="122" x2="220" y2="148"
              stroke="#374151" stroke-width="4" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 4)}"/>
        <!-- Mano derecha -->
        <circle cx="222" cy="150" r="4" fill="#f5e6d3" stroke="#374151" stroke-width="2"
                visibility="{vis(wrong_guesses >= 4)}"/>

        <!-- Pierna izquierda -->
        <line x1="185" y1="168" x2="155" y2="205"
              stroke="#374151" stroke-width="4" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 5)}"/>
        <!-- Pie izquierdo -->
        <line x1="155" y1="205" x2="140" y2="208"
              stroke="#374151" stroke-width="3" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 5)}"/>

        <!-- Pierna derecha -->
        <line x1="185" y1="168" x2="215" y2="205"
              stroke="#374151" stroke-width="4" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 6)}"/>
        <!-- Pie derecho -->
        <line x1="215" y1="205" x2="230" y2="208"
              stroke="#374151" stroke-width="3" stroke-linecap="round"
              visibility="{vis(wrong_guesses >= 6)}"/>
    </svg>
    """


def extract_words_from_docx(file_bytes: bytes) -> list:
    doc = Document(io.BytesIO(file_bytes))
    phrases = []
    for para in doc.paragraphs:
        line = para.text.upper().strip()
        # Remove invalid chars but keep spaces
        cleaned = re.sub(r'[^A-ZÁÉÍÓÚÜÑ ]', '', line)
        # Collapse multiple spaces
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


def handle_guess(letter: str):
    if st.session_state.is_game_over or letter in st.session_state.guessed_letters:
        return
    st.session_state.guessed_letters.add(letter)
    if letter in st.session_state.selected_word:
        st.session_state.correct_letters.add(letter)
        if all(l in st.session_state.correct_letters for l in st.session_state.selected_word if l != ' '):
            st.session_state.is_game_over = True
            st.session_state.is_win = True
    else:
        st.session_state.wrong_guesses += 1
        if st.session_state.wrong_guesses >= MAX_WRONG_GUESSES:
            st.session_state.is_game_over = True
            st.session_state.is_win = False


def render_word():
    word = st.session_state.selected_word
    correct = st.session_state.correct_letters
    is_game_over = st.session_state.is_game_over
    is_win = st.session_state.is_win

    spans = []
    for letter in word:
        if letter == ' ':
            spans.append(
                '<span style="display:inline-block;min-width:1.2rem;height:2.8rem;'
                'margin:4px 6px"></span>'
            )
            continue
        revealed = letter in correct
        show_red = is_game_over and not is_win and not revealed
        if revealed:
            border_color, text, color = '#9ca3af', letter, '#1f2937'
        elif show_red:
            border_color, text, color = '#f87171', letter, '#ef4444'
        else:
            border_color, text, color = '#9ca3af', '&nbsp;', 'transparent'

        spans.append(
            f'<span style="display:inline-block;border-bottom:4px solid {border_color};'
            f'margin:4px 6px;min-width:2rem;height:2.8rem;text-align:center;'
            f'font-size:2rem;font-family:monospace;color:{color};font-weight:bold;'
            f'line-height:2.8rem">{text}</span>'
        )

    st.markdown(
        f'<div style="text-align:center;min-height:4rem;margin:1.5rem 0;flex-wrap:wrap">'
        f'{"".join(spans)}</div>',
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
        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
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


if __name__ == "__main__":
    main()
