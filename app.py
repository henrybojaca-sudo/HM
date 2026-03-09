import io
import random

import pandas as pd
import streamlit as st

from Cds_Mundo import data as default_data

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="CDS Game",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Estilos ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer     {visibility: hidden;}

/* --- Título --- */
.title-block { text-align: center; padding: 18px 0 6px; }
.title-block h1 {
    font-size: 2.8rem; font-weight: 900; letter-spacing: 4px;
    color: #FFFFFF; margin: 0;
}
.title-block p { color: #888; font-size: 0.9rem; margin: 4px 0 0; }

/* --- Score --- */
.score-row { display: flex; justify-content: center; gap: 24px; margin: 12px 0 20px; }
.score-chip {
    background: #1a1d2e; border-radius: 20px;
    padding: 8px 22px; font-size: 1rem; color: #fff; font-weight: 600;
    border: 1px solid #2e3250;
}
.score-chip .val  { color: #4CAF50; }
.score-chip .val2 { color: #FFD700; }

/* --- Pregunta --- */
.question {
    text-align: center; font-size: 1.1rem; color: #bbb; margin-bottom: 16px;
}
.question strong { color: #fff; }

/* --- Tarjetas de país --- */
.card {
    background: linear-gradient(145deg, #1a1d2e, #232742);
    border-radius: 18px; padding: 26px 16px; text-align: center;
    min-height: 185px; display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    border: 1px solid #2e3250;
}
.card-label { font-size: 0.75rem; font-weight: 700; letter-spacing: 3px; color: #666; margin-bottom: 8px; }
.card-flag  { line-height: 1; margin-bottom: 6px; min-height: 60px; display:flex; align-items:center; justify-content:center; }
.card-name  { font-size: 1.25rem; font-weight: 800; color: #fff; }
.card-region { font-size: 0.75rem; color: #666; margin-top: 3px; }
.card-cds {
    margin-top: 10px; font-size: 1rem; font-weight: 700; color: #FF6B6B;
    background: rgba(255,107,107,0.12); border-radius: 8px; padding: 4px 12px;
}

/* --- VS --- */
.vs-wrap { display:flex; align-items:center; justify-content:center; height:100%; }
.vs-text { font-size: 2rem; font-weight: 900; color: #FF4B4B; }

/* --- Feedback --- */
.fb-correct {
    background: rgba(40,167,69,0.12); border: 2px solid #28a745;
    border-radius: 12px; padding: 16px 20px; text-align: center;
    color: #4dff7c; font-size: 1.25rem; font-weight: 700; margin-top: 18px;
}
.fb-wrong {
    background: rgba(220,53,69,0.12); border: 2px solid #dc3545;
    border-radius: 12px; padding: 16px 20px; text-align: center;
    color: #ff6b6b; font-size: 1.25rem; font-weight: 700; margin-top: 18px;
}
.fb-detail { font-size: 0.88rem; color: #ccc; margin-top: 6px; font-weight: 400; }

/* --- Game Over --- */
.go-box {
    text-align: center; background: #1a1d2e;
    border-radius: 18px; padding: 40px 30px; margin: 16px 0;
    border: 1px solid #2e3250;
}
.go-box h2   { color: #FF4B4B; font-size: 2.2rem; margin-bottom: 6px; }
.go-score    { font-size: 5rem; font-weight: 900; color: #FFD700; line-height: 1; }
.go-label    { color: #888; font-size: 0.95rem; margin-top: 6px; }
.go-hs       { color: #4CAF50; font-size: 1rem; margin-top: 14px; }
.go-tip      { color: #666; font-size: 0.82rem; margin-top: 18px; font-style: italic; }

/* --- Info CDS --- */
.info-box {
    background: #1a1d2e; border-radius: 12px; padding: 14px 18px;
    border-left: 3px solid #4CAF50; margin-top: 28px; font-size: 0.83rem; color: #888;
}
.info-box strong { color: #aaa; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _build_iso_lookup():
    """Build a name→iso/region lookup from default data for matching uploaded countries."""
    return {entry["pais"].lower(): entry for entry in default_data}


_ISO_LOOKUP = _build_iso_lookup()


def _parse_excel(file_bytes: bytes) -> list:
    """Parse an Excel file and return a list of country dicts.

    Expects country names in column A and CDS values in column C.
    """
    df = pd.read_excel(io.BytesIO(file_bytes), header=None, engine="openpyxl")
    countries = []
    for _, row in df.iterrows():
        try:
            name = str(row.iloc[0]).strip()
            cds_val = float(row.iloc[2])
        except (ValueError, IndexError):
            continue
        if not name or name.lower() in ("nan", "país", "pais", "country"):
            continue
        match = _ISO_LOOKUP.get(name.lower(), {})
        countries.append({
            "pais": name,
            "region": match.get("region", ""),
            "iso": match.get("iso", ""),
            "cds": cds_val,
        })
    return countries


def get_active_data() -> list:
    return st.session_state.get("custom_data") or default_data


def get_random_country(exclude=None):
    active = get_active_data()
    options = [x for x in active if x != exclude] if exclude else active[:]
    return random.choice(options)


def card_html(label, country, reveal=False):
    cds_html = f'<div class="card-cds">CDS: {country["cds"]} bps</div>' if reveal else ""
    iso = country.get("iso", "")
    flag_html = (
        f'<img src="https://flagcdn.com/80x60/{iso}.png" '
        f'     srcset="https://flagcdn.com/160x120/{iso}.png 2x" '
        f'     width="80" height="60" alt="{country["pais"]}" '
        f'     style="border-radius:6px; object-fit:cover;">'
        if iso else ""
    )
    return f"""
    <div class="card">
        <div class="card-label">{label}</div>
        <div class="card-flag">{flag_html}</div>
        <div class="card-name">{country['pais']}</div>
        <div class="card-region">{country.get('region','')}</div>
        {cds_html}
    </div>"""


# ── Sidebar: carga de Excel ───────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 Datos personalizados")
    st.markdown(
        "Sube un archivo **Excel (.xlsx)** con tus propios valores de CDS:\n"
        "- **Columna A**: nombre del país\n"
        "- **Columna C**: valor del CDS (bps)"
    )
    uploaded = st.file_uploader("Seleccionar archivo .xlsx", type=["xlsx"])

    if uploaded is not None:
        try:
            parsed = _parse_excel(uploaded.read())
            if len(parsed) < 2:
                st.error("El archivo debe contener al menos 2 países válidos.")
            else:
                if st.session_state.get("custom_data") != parsed:
                    st.session_state.custom_data = parsed
                    # Reset game when new data is loaded
                    for key in ("phase", "score", "high_score",
                                "country_a", "country_b",
                                "last_a", "last_b", "next_b", "correct"):
                        st.session_state.pop(key, None)
                    st.rerun()
                st.success(f"✅ {len(parsed)} países cargados desde Excel.")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

    if st.session_state.get("custom_data"):
        if st.button("🔄 Usar datos por defecto", use_container_width=True):
            st.session_state.custom_data = None
            for key in ("phase", "score", "high_score",
                        "country_a", "country_b",
                        "last_a", "last_b", "next_b", "correct"):
                st.session_state.pop(key, None)
            st.rerun()
        st.caption(f"Usando {len(st.session_state.custom_data)} países del Excel.")
    else:
        st.caption(f"Usando {len(default_data)} países por defecto.")


# ── Estado inicial ────────────────────────────────────────────────────────────
def _init():
    if "phase" not in st.session_state:
        a = get_random_country()
        b = get_random_country(exclude=a)
        st.session_state.update(
            phase="playing",
            score=0,
            high_score=0,
            country_a=a,
            country_b=b,
            last_a=None,
            last_b=None,
            next_b=None,
            correct=None,
        )

_init()


# ── Callbacks ─────────────────────────────────────────────────────────────────
def handle_guess(choice):
    a, b = st.session_state.country_a, st.session_state.country_b
    a_cds, b_cds = float(a["cds"]), float(b["cds"])
    is_correct = (choice == "A" and a_cds > b_cds) or (choice == "B" and b_cds >= a_cds)

    st.session_state.last_a = a
    st.session_state.last_b = b
    st.session_state.correct = is_correct

    if is_correct:
        st.session_state.score += 1
        if st.session_state.score > st.session_state.high_score:
            st.session_state.high_score = st.session_state.score
        st.session_state.next_b = get_random_country(exclude=b)
        st.session_state.phase = "result_correct"
    else:
        st.session_state.phase = "game_over"


def handle_next():
    st.session_state.country_a = st.session_state.last_b
    st.session_state.country_b = st.session_state.next_b
    st.session_state.phase = "playing"


def handle_replay():
    a = get_random_country()
    b = get_random_country(exclude=a)
    st.session_state.update(
        phase="playing",
        score=0,
        country_a=a,
        country_b=b,
        last_a=None,
        last_b=None,
        next_b=None,
        correct=None,
    )


# ── Render ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="title-block">
    <h1>📊 CDS GAME</h1>
    <p>Riesgo crediticio soberano — Credit Default Swaps</p>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="score-row">
    <div class="score-chip">Puntos&nbsp;<span class="val">{st.session_state.score}</span></div>
    <div class="score-chip">Récord&nbsp;<span class="val2">{st.session_state.high_score}</span></div>
</div>""", unsafe_allow_html=True)

phase = st.session_state.phase

# ─── JUGANDO ──────────────────────────────────────────────────────────────────
if phase == "playing":
    st.markdown(
        '<p class="question">¿Cuál país tiene <strong>MAYOR</strong> riesgo crediticio?</p>',
        unsafe_allow_html=True,
    )

    col_a, col_vs, col_b = st.columns([5, 1, 5])
    with col_a:
        st.markdown(card_html("PAÍS A", st.session_state.country_a), unsafe_allow_html=True)
    with col_vs:
        st.markdown('<div class="vs-wrap"><div class="vs-text">VS</div></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(card_html("PAÍS B", st.session_state.country_b), unsafe_allow_html=True)

    st.write("")
    btn_a, btn_b = st.columns(2)
    with btn_a:
        st.button("🔴 A tiene más riesgo", use_container_width=True,
                  on_click=handle_guess, args=("A",), type="primary")
    with btn_b:
        st.button("🔴 B tiene más riesgo", use_container_width=True,
                  on_click=handle_guess, args=("B",), type="primary")

# ─── CORRECTO ─────────────────────────────────────────────────────────────────
elif phase == "result_correct":
    a, b = st.session_state.last_a, st.session_state.last_b
    winner = a if float(a["cds"]) > float(b["cds"]) else b

    st.markdown(
        '<p class="question">Resultado de la ronda</p>',
        unsafe_allow_html=True,
    )

    col_a, col_vs, col_b = st.columns([5, 1, 5])
    with col_a:
        st.markdown(card_html("PAÍS A", a, reveal=True), unsafe_allow_html=True)
    with col_vs:
        st.markdown('<div class="vs-wrap"><div class="vs-text">VS</div></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(card_html("PAÍS B", b, reveal=True), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="fb-correct">
        ✅ ¡CORRECTO!
        <div class="fb-detail">
            <strong>{winner['pais']}</strong> tiene el CDS más alto
            &nbsp;({winner['cds']} bps)
        </div>
    </div>""", unsafe_allow_html=True)

    st.write("")
    st.button("▶ Siguiente ronda", use_container_width=True,
              on_click=handle_next, type="primary")

# ─── GAME OVER ────────────────────────────────────────────────────────────────
elif phase == "game_over":
    a, b = st.session_state.last_a, st.session_state.last_b
    winner = a if float(a["cds"]) > float(b["cds"]) else b

    col_a, col_vs, col_b = st.columns([5, 1, 5])
    with col_a:
        st.markdown(card_html("PAÍS A", a, reveal=True), unsafe_allow_html=True)
    with col_vs:
        st.markdown('<div class="vs-wrap"><div class="vs-text">VS</div></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(card_html("PAÍS B", b, reveal=True), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="fb-wrong">
        ❌ INCORRECTO
        <div class="fb-detail">
            <strong>{winner['pais']}</strong> tenía el CDS más alto
            &nbsp;({winner['cds']} bps)
        </div>
    </div>""", unsafe_allow_html=True)

    is_new_record = st.session_state.score > 0 and st.session_state.score == st.session_state.high_score
    hs_html = (
        '<div class="go-hs">🏆 ¡Nuevo récord!</div>'
        if is_new_record else ""
    )
    st.markdown(f"""
    <div class="go-box">
        <h2>JUEGO TERMINADO</h2>
        <div class="go-score">{st.session_state.score}</div>
        <div class="go-label">puntos</div>
        {hs_html}
        <div class="go-tip">Récord de sesión: {st.session_state.high_score} puntos</div>
    </div>""", unsafe_allow_html=True)

    st.button("🔄 Jugar de nuevo", use_container_width=True,
              on_click=handle_replay, type="primary")

# ─── Info pie de página ───────────────────────────────────────────────────────
with st.expander("ℹ️ ¿Qué es el CDS?"):
    st.markdown(
        """
        Un **Credit Default Swap (CDS)** es un instrumento financiero que funciona como un
        seguro contra el incumplimiento de pago de un país (deuda soberana).
        Se mide en **puntos base (bps)** — cuanto mayor el valor, mayor el riesgo percibido
        por los mercados financieros.

        *Los valores mostrados son aproximados y de carácter educativo.*
        """
    )
