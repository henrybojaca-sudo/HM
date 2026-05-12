import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
import math, wave, struct, io, base64

st.set_page_config(
    page_title="CDS Challenge",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

COUNTRY_ISO = {
    "Estados Unidos":"us","Brasil":"br","Colombia":"co","Chile":"cl",
    "México":"mx","Panamá":"pa","Perú":"pe","Argentina":"ar",
    "Ecuador":"ec","Costa Rica":"cr","Canadá":"ca","El Salvador":"sv",
    "Guatemala":"gt","Uruguay":"uy","Nicaragua":"ni","Reino Unido":"gb",
    "Francia":"fr","Alemania":"de","Italia":"it","España":"es",
    "Portugal":"pt","Suecia":"se","Países Bajos":"nl","Suiza":"ch",
    "Grecia":"gr","Austria":"at","Bélgica":"be","Bulgaria":"bg",
    "Croacia":"hr","Dinamarca":"dk","Egipto":"eg","Finlandia":"fi",
    "Hungría":"hu","Israel":"il","Kazajistán":"kz","Polonia":"pl",
    "Qatar":"qa","Rumanía":"ro","Eslovaquia":"sk","Sudáfrica":"za",
    "Checa":"cz","Eslovenia":"si","Letonia":"lv","Lituania":"lt",
    "Estonia":"ee","Serbia":"rs","Bahrein":"bh","Nigeria":"ng",
    "Argelia":"dz","Irak":"iq","Chipre":"cy","Dubai":"ae",
    "Irlanda":"ie","Noruega":"no","Arabia Saudita":"sa","Kuwait":"kw",
    "Omán":"om","Tunisia":"tn","Turquía":"tr","Islanda":"is",
    "Abu Dhabi":"ae","Marruecos":"ma","Ghana":"gh","Gabón":"ga",
    "Kenia":"ke","Angola":"ao","Camerún":"cm","Ruanda":"rw",
    "Senegal":"sn","Zambia":"zm","Etiopía":"et","Namibia":"na",
    "Japón":"jp","Australia":"au","N. Zelanda":"nz","Sur Corea":"kr",
    "China":"cn","Hong Kong":"hk","India":"in","Indonesia":"id",
    "Malasia":"my","Filipinas":"ph","Pakistán":"pk","Tailandia":"th",
    "Vietnam":"vn","Mongolia":"mn",
}

DEFAULT_DATA = [
    ("Estados Unidos",40.33),("Brasil",125.10),("Colombia",219.29),
    ("México",93.33),("Argentina",598.67),("Chile",51.01),
    ("Perú",74.16),("Panamá",101.00),("Canadá",17.70),
    ("Ecuador",402.64),("Uruguay",56.16),("Costa Rica",129.29),
    ("El Salvador",320.90),("Guatemala",120.74),("Nicaragua",450.27),
    ("Reino Unido",20.56),("Francia",30.05),("Alemania",9.74),
    ("Italia",32.22),("España",18.43),("Portugal",17.60),
    ("Suecia",8.87),("Países Bajos",9.37),("Suiza",12.77),
    ("Grecia",31.75),("Turquía",235.81),("Arabia Saudita",63.78),
    ("Egipto",326.35),("Sudáfrica",150.47),("Bahrein",252.32),
    ("Abu Dhabi",43.59),("Rumanía",163.79),("Qatar",35.05),
    ("Israel",68.37),("Dubai",84.91),("Hungría",82.24),
    ("Nigeria",273.51),("Polonia",56.42),("Omán",69.51),
    ("Kuwait",59.86),("Bélgica",19.98),("Kenia",451.90),
    ("Serbia",147.60),("Kazajistán",76.02),("Checa",34.02),
    ("Marruecos",74.83),("Angola",408.76),("Bulgaria",53.54),
    ("Eslovaquia",46.71),("Croacia",56.71),("Irlanda",16.85),
    ("Eslovenia",41.64),("Austria",13.30),("Dinamarca",9.85),
    ("Noruega",8.73),("Irak",436.62),("Ghana",342.14),
    ("Senegal",1165.41),("Lituania",57.85),("Estonia",71.36),
    ("Finlandia",13.60),("Letonia",60.54),("Argelia",88.89),
    ("Etiopía",3425.68),("Chipre",47.69),("Tunisia",691.23),
    ("Zambia",360.95),("Islanda",42.51),("Ruanda",307.20),
    ("Camerún",514.22),("Gabón",687.93),("Namibia",280.26),
    ("Japón",27.80),("Australia",14.66),("N. Zelanda",16.86),
    ("Sur Corea",27.48),("Indonesia",86.78),("China",42.76),
    ("Filipinas",76.97),("India",57.76),("Malasia",36.85),
    ("Hong Kong",27.21),("Tailandia",52.60),("Pakistán",452.13),
    ("Vietnam",95.37),("Mongolia",212.23),
]

NON_COUNTRIES = {"América","EMEA","Asia/Pacífico","Name"}

@st.cache_data
def _gameover_wav() -> bytes:
    SR = 22050
    NOTES = [
        (523.25, 0.20), (392.00, 0.20), (0, 0.20),
        (415.30, 0.40), (392.00, 0.40), (0, 0.20),
        (349.23, 0.60), (329.63, 0.30), (293.66, 0.30), (261.63, 1.00),
    ]
    samples = []
    for freq, dur in NOTES:
        n = int(SR * dur)
        if freq == 0:
            samples.extend([0] * n)
        else:
            for i in range(n):
                env = min(1.0, i / (SR * 0.008)) * max(0.0, 1.0 - i / n * 0.15)
                v = env * 0.30 * (1 if math.sin(2 * math.pi * freq * i / SR) > 0 else -1)
                samples.append(max(-32767, min(32767, int(v * 32767))))
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    return buf.getvalue()

@st.cache_data
def _mario_wav() -> bytes:
    SR = 22050
    T = 60.0 / 185
    MELODY = [
        (659.25,.5),(659.25,.5),(0,.5),(659.25,.5),(0,.5),(523.25,.5),(659.25,1),
        (783.99,1),(0,1),(392.00,1),(0,1),
        (523.25,1.5),(0,.5),(392.00,1.5),(0,.5),(329.63,1.5),(0,.5),
        (440.00,1),(0,.5),(493.88,1),(0,.5),(466.16,.5),(440.00,1),
        (392.00,.67),(659.25,.67),(783.99,.67),
        (880.00,1),(0,.5),(698.46,.5),(783.99,.5),
        (0,.5),(659.25,1),(0,.5),(523.25,.5),(587.33,.5),(493.88,1.5),(0,.5),
        (523.25,1.5),(0,.5),(392.00,1.5),(0,.5),(329.63,1.5),(0,.5),
        (440.00,1),(0,.5),(493.88,1),(0,.5),(466.16,.5),(440.00,1),
        (392.00,.67),(659.25,.67),(783.99,.67),
        (880.00,1),(0,.5),(698.46,.5),(783.99,.5),
        (0,.5),(659.25,1),(0,.5),(523.25,.5),(587.33,.5),(493.88,1.5),(0,.5),
        (659.25,.5),(523.25,.5),(0,.5),(440.00,.5),(0,1),(415.30,.5),(392.00,.5),
        (0,.5),(493.88,.5),(0,.5),(466.16,.5),(440.00,.5),(0,.5),(523.25,.5),(0,.5),
        (587.33,.5),(523.25,.5),(587.33,1),(0,.5),(587.33,.5),(523.25,.5),(440.00,.5),
        (0,.5),(392.00,.5),(329.63,.5),(392.00,.5),(440.00,1.5),(0,.5),
        (698.46,.5),(698.46,1),(698.46,1),
        (0,.5),(659.25,.5),(659.25,.5),(659.25,.5),
        (0,.5),(523.25,.5),(659.25,1),
        (783.99,1),(0,1),(392.00,1),(0,1),
    ]
    samples = []
    for freq, beats in MELODY:
        n = int(SR * beats * T)
        if freq == 0:
            samples.extend([0] * n)
        else:
            for i in range(n):
                env = min(1.0, i / (SR * 0.008)) * max(0.0, 1.0 - i / n * 0.12)
                v = env * 0.28 * (1 if math.sin(2 * math.pi * freq * i / SR) > 0 else -1)
                samples.append(max(-32767, min(32767, int(v * 32767))))
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
    return buf.getvalue()


def load_excel(f):
    try:
        raw = pd.read_excel(f, header=None)
        rows = []
        for _, row in raw.iterrows():
            name = str(row[0]).strip()
            if name in NON_COUNTRIES or name == "nan":
                continue
            try:
                rows.append((name, round(float(row[1]), 2)))
            except (TypeError, ValueError, IndexError):
                continue
        if len(rows) < 2:
            st.error("Necesitas al menos 2 países con CDS en columna B.")
            return None
        return pd.DataFrame(rows, columns=["Pais","CDS"]).reset_index(drop=True)
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def default_df():
    return pd.DataFrame(DEFAULT_DATA, columns=["Pais","CDS"])


def pick_pair(df, used):
    idx = list(df.index)
    cands = [(i,j) for i in idx for j in idx if i<j and (i,j) not in used]
    return random.choice(cands) if cands else None


def init_state():
    for k,v in {"df":None,"score":0,"best":0,"game_over":False,
                "game_started":False,"current_pair":None,"used_pairs":set(),
                "feedback":None,"correct_country":None,"round_active":True}.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.df is None:
        st.session_state.df = default_df()


def reset_game():
    st.session_state.update({"score":0,"game_over":False,"game_started":True,
        "current_pair":None,"used_pairs":set(),"feedback":None,
        "correct_country":None,"round_active":True})


def advance():
    st.session_state.feedback = None
    st.session_state.correct_country = None
    st.session_state.round_active = True
    pair = pick_pair(st.session_state.df, st.session_state.used_pairs)
    if pair is None:
        st.session_state.game_over = True
        st.session_state.feedback = "completed"
    else:
        st.session_state.current_pair = pair
        st.session_state.used_pairs.add(pair)


def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.stApp{background:#0a0f1e;}
section[data-testid="stSidebar"]{background:#0d1426;}
.game-header{text-align:center;padding:28px 0 8px;margin-bottom:4px;}
.game-title{font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:#fff;letter-spacing:-.5px;margin:0;line-height:1.1;}
.game-title span{color:#fbbf24;}
.game-subtitle{color:#64748b;font-size:.85rem;margin-top:6px;letter-spacing:.05em;text-transform:uppercase;}
.score-row{display:flex;justify-content:center;gap:10px;margin:16px 0 24px;flex-wrap:wrap;}
.pill{display:flex;align-items:center;gap:6px;padding:6px 16px;border-radius:100px;font-size:.88rem;font-weight:600;}
.pill-score{background:rgba(251,191,36,.12);border:1px solid rgba(251,191,36,.3);color:#fbbf24;}
.pill-best{background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.25);color:#34d399;}
.pill-countries{background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.25);color:#818cf8;}
.question-label{text-align:center;color:#94a3b8;font-size:.9rem;font-weight:500;margin-bottom:20px;letter-spacing:.03em;text-transform:uppercase;}
.vs-divider{display:flex;flex-direction:column;align-items:center;justify-content:center;height:160px;}
.vs-text{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;color:#334155;letter-spacing:.15em;}
.vs-line{width:1px;height:28px;background:linear-gradient(to bottom,transparent,#334155,transparent);margin:4px 0;}
.flag-choice-card{
    position:relative;border-radius:16px;overflow:hidden;height:160px;
    box-shadow:0 6px 28px rgba(0,0,0,0.55);
    border:2px solid #1e293b;
    transition:border-color .2s, box-shadow .2s, transform .15s;
}
.flag-choice-card img{width:100%;height:100%;object-fit:cover;display:block;}
.fcc-gradient{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.88) 0%,rgba(0,0,0,0.3) 55%,rgba(0,0,0,0.05) 100%);}
.fcc-name{position:absolute;bottom:12px;left:0;right:0;text-align:center;color:#fff;font-family:'Syne',sans-serif;font-weight:800;font-size:1.05rem;text-shadow:0 2px 10px rgba(0,0,0,1);letter-spacing:-.2px;}
.fcc-hint{position:absolute;top:10px;right:10px;background:rgba(255,255,255,0.15);backdrop-filter:blur(4px);border-radius:20px;padding:3px 9px;font-size:.65rem;color:rgba(255,255,255,0.8);font-weight:600;letter-spacing:.05em;}
.fcc-placeholder{width:100%;height:100%;background:#1e293b;display:flex;align-items:center;justify-content:center;font-size:3rem;}
.flag-result-card{position:relative;border-radius:16px;overflow:hidden;height:160px;box-shadow:0 4px 20px rgba(0,0,0,0.5);}
.flag-result-card img{width:100%;height:100%;object-fit:cover;display:block;}
.flag-result-card .fcc-gradient{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.88) 0%,rgba(0,0,0,0.3) 55%,rgba(0,0,0,0.05) 100%);}
.flag-result-card .fcc-name{position:absolute;bottom:12px;left:0;right:0;text-align:center;color:#fff;font-family:'Syne',sans-serif;font-weight:800;font-size:1.05rem;text-shadow:0 2px 10px rgba(0,0,0,1);}
div[data-testid="stButton"]>button{border-radius:12px!important;font-family:'DM Sans',sans-serif!important;font-weight:600!important;font-size:.9rem!important;padding:10px 16px!important;width:100%!important;transition:all .15s ease!important;border:1.5px solid #1e3a5f!important;background:linear-gradient(135deg,#0f2a4a,#0d1f3c)!important;color:#93c5fd!important;}
div[data-testid="stButton"]>button:hover{border-color:#3b82f6!important;color:#bfdbfe!important;transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(59,130,246,.2)!important;}
div[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#1d4ed8,#1e40af)!important;border-color:#3b82f6!important;color:#fff!important;}
div[data-testid="stButton"]>button[kind="primary"]:hover{background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;box-shadow:0 6px 24px rgba(37,99,235,.35)!important;}
.fb-box{border-radius:14px;padding:14px 18px;text-align:center;font-weight:600;font-size:.95rem;margin:16px 0 12px;line-height:1.5;}
.fb-correct{background:rgba(52,211,153,.08);border:1.5px solid rgba(52,211,153,.3);color:#34d399;}
.fb-wrong{background:rgba(239,68,68,.08);border:1.5px solid rgba(239,68,68,.3);color:#f87171;}
.fb-done{background:rgba(251,191,36,.08);border:1.5px solid rgba(251,191,36,.3);color:#fbbf24;}
.cds-reveal{display:flex;justify-content:center;gap:12px;margin:8px 0 16px;flex-wrap:wrap;}
.cds-badge{padding:4px 14px;border-radius:100px;font-size:.82rem;font-weight:600;}
.cds-winner{background:rgba(52,211,153,.12);border:1px solid rgba(52,211,153,.3);color:#34d399;}
.cds-loser{background:rgba(100,116,139,.12);border:1px solid rgba(100,116,139,.25);color:#64748b;}
.game-divider{border:none;border-top:1px solid #1e293b;margin:20px 0;}
.welcome-box{text-align:center;padding:48px 24px;color:#475569;}
.welcome-icon{font-size:3.5rem;margin-bottom:16px;}
.welcome-text{font-size:1rem;font-weight:500;color:#64748b;}
.welcome-sub{font-size:.83rem;color:#334155;margin-top:8px;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.5rem;padding-bottom:2rem;}
</style>
    """, unsafe_allow_html=True)


def render_flag_card(name, clickable=True, choice_key=""):
    iso = COUNTRY_ISO.get(name, "")
    flag_url = f"https://flagcdn.com/w160/{iso}.png" if iso else ""

    if flag_url:
        st.markdown(
            f'<div style="width:100%;height:160px;border-radius:14px;overflow:hidden;'
            f'box-shadow:0 6px 28px rgba(0,0,0,0.55);border:2px solid #1e293b;">'
            f'<img src="{flag_url}" alt="{name}" style="width:100%;height:100%;object-fit:cover;display:block"></div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="width:100%;height:160px;border-radius:14px;background:#1e293b;'
            'display:flex;align-items:center;justify-content:center;font-size:3rem">🏳️</div>',
            unsafe_allow_html=True)

    if clickable:
        return st.button(name, key=f"flag_btn_{choice_key}", use_container_width=True)
    else:
        st.markdown(
            f'<div style="text-align:center;color:#94a3b8;font-weight:700;'
            f'font-size:.95rem;padding:8px 0">{name}</div>',
            unsafe_allow_html=True)
        return False


def render_flag_small(name):
    iso = COUNTRY_ISO.get(name, "")
    flag_url = f"https://flagcdn.com/w160/{iso}.png" if iso else ""
    if flag_url:
        st.markdown(
            f'<div style="width:100%;height:100px;border-radius:10px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.4)">'
            f'<img src="{flag_url}" alt="{name}" style="width:100%;height:100%;object-fit:cover;display:block"></div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="width:100%;height:100px;border-radius:10px;background:#1e293b;'
            'display:flex;align-items:center;justify-content:center;font-size:2.5rem">🏳️</div>',
            unsafe_allow_html=True)


def main():
    init_state()
    inject_css()

    st.markdown(
        '<div class="game-header">'
        '<div class="game-title">¿Quién tiene mayor <span>riesgo país</span>?</div>'
        '<div class="game-subtitle">Credit Default Swap Challenge · Posgrado en Finanzas</div>'
        '</div>', unsafe_allow_html=True)

    n = len(st.session_state.df)
    st.markdown(
        f'<div class="score-row">'
        f'<div class="pill pill-score">🔥 Racha: {st.session_state.score}</div>'
        f'<div class="pill pill-best">🏆 Mejor: {st.session_state.best}</div>'
        f'<div class="pill pill-countries">🌍 {n} países</div>'
        f'</div>', unsafe_allow_html=True)

    if st.session_state.feedback != "wrong":
        _, cm, _ = st.columns([1, 4, 1])
        with cm:
            st.markdown(
                '<div style="text-align:center;color:#475569;font-size:.72rem;'
                'letter-spacing:.07em;text-transform:uppercase;margin-bottom:4px">'
                '🎵 Música del juego · haz clic en ▶</div>',
                unsafe_allow_html=True)
            st.audio(_mario_wav(), format="audio/wav", loop=True)

    with st.sidebar:
        st.markdown("### 📂 Datos")
        st.caption("Sube tu propio archivo Excel con CDS actualizados")
        up = st.file_uploader("Excel (col A=País, col B=CDS)", type=["xlsx"], label_visibility="collapsed")
        if up:
            dfn = load_excel(up)
            if dfn is not None:
                st.session_state.df = dfn
                reset_game(); advance()
                st.success(f"✅ {len(dfn)} países cargados"); st.rerun()
        st.divider()
        if st.checkbox("📊 Ranking CDS"):
            d = st.session_state.df.copy(); d.columns = ["País","CDS (pb)"]
            st.dataframe(d.sort_values("CDS (pb)",ascending=False).reset_index(drop=True),
                         hide_index=True, use_container_width=True, height=480)
        st.divider()
        st.caption("**CDS** = Credit Default Swap. Mayor CDS = Mayor riesgo soberano.")

    c1, c2, c3 = st.columns([2, 3, 2])
    with c2:
        label = "🎮 Nuevo juego" if st.session_state.game_started else "▶️ Iniciar juego"
        if st.button(label, type="primary", use_container_width=True):
            reset_game(); advance(); st.rerun()

    if st.session_state.game_started and not st.session_state.game_over:
        pair = st.session_state.current_pair
        if not pair:
            return
        df = st.session_state.df
        ia, ib = pair
        ca, cb = df.loc[ia,"Pais"], df.loc[ib,"Pais"]
        cds_a, cds_b = df.loc[ia,"CDS"], df.loc[ib,"CDS"]

        st.markdown('<hr class="game-divider">', unsafe_allow_html=True)
        st.markdown('<div class="question-label">¿Cuál tiene el CDS más alto? — haz clic en la bandera</div>', unsafe_allow_html=True)

        col_a, col_vs, col_b = st.columns([5, 1, 5])
        with col_a:
            clicked_a = render_flag_card(ca, clickable=st.session_state.round_active, choice_key="a")
        with col_vs:
            st.markdown('<div class="vs-divider"><div class="vs-line"></div><div class="vs-text">VS</div><div class="vs-line"></div></div>', unsafe_allow_html=True)
        with col_b:
            clicked_b = render_flag_card(cb, clickable=st.session_state.round_active, choice_key="b")

        if st.session_state.round_active and (clicked_a or clicked_b):
            correct = ca if cds_a > cds_b else cb
            chosen = ca if clicked_a else cb
            if chosen == correct:
                st.session_state.score += 1
                st.session_state.best = max(st.session_state.best, st.session_state.score)
                st.session_state.feedback = "correct"
            else:
                st.session_state.feedback = "wrong"
                st.session_state.game_over = True
            st.session_state.correct_country = correct
            st.session_state.round_active = False
            st.rerun()

        if st.session_state.feedback == "correct":
            cn = st.session_state.correct_country
            c_cds = df.loc[df["Pais"]==cn,"CDS"].values[0]
            ot = cb if cn==ca else ca
            o_cds = df.loc[df["Pais"]==ot,"CDS"].values[0]
            st.markdown(f'<div class="fb-box fb-correct">✅ ¡Correcto! <b>{cn}</b> tiene mayor riesgo soberano</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cds-reveal"><div class="cds-badge cds-winner">🔴 {cn}: {c_cds:,.1f} pb</div><div class="cds-badge cds-loser">⚪ {ot}: {o_cds:,.1f} pb</div></div>', unsafe_allow_html=True)
            _, cn2, _ = st.columns([2, 3, 2])
            with cn2:
                if st.button("Siguiente →", type="primary", use_container_width=True):
                    advance(); st.rerun()

    if st.session_state.game_over:
        fb = st.session_state.feedback
        sc = st.session_state.score
        bst = st.session_state.best
        pair = st.session_state.current_pair
        df = st.session_state.df

        if fb == "completed":
            st.markdown(f'<div class="fb-box fb-done">🎉 ¡Completaste todos los pares! · Racha: <b>{sc}</b> · Récord: <b>{bst}</b></div>', unsafe_allow_html=True)
        elif fb == "wrong" and pair:
            ia, ib = pair
            ca, cb = df.loc[ia,"Pais"], df.loc[ib,"Pais"]
            cds_a, cds_b = df.loc[ia,"CDS"], df.loc[ib,"CDS"]
            cn = st.session_state.correct_country
            c_cds = df.loc[df["Pais"]==cn,"CDS"].values[0]
            ot = cb if cn==ca else ca
            o_cds = df.loc[df["Pais"]==ot,"CDS"].values[0]
            st.markdown(f'<div class="fb-box fb-wrong">❌ Racha detenida en <b>{sc}</b> acierto{"s" if sc!=1 else ""}<br><small>Respuesta correcta: <b>{cn}</b> ({c_cds:,.1f} pb) vs {ot} ({o_cds:,.1f} pb)</small></div>', unsafe_allow_html=True)
            _go_b64 = base64.b64encode(_gameover_wav()).decode()
            components.html(f"""<script>
try {{ parent.document.querySelectorAll('audio').forEach(function(a){{ a.pause(); a.currentTime=0; }}); }} catch(e) {{}}
var _go=new Audio('data:audio/wav;base64,{_go_b64}'); _go.play();
</script>""", height=0, scrolling=False)
            st.markdown("<br>", unsafe_allow_html=True)
            a2, v2, b2 = st.columns([5, 1, 5])
            with a2:
                render_flag_small(ca)
                col = "#f87171" if ca!=cn else "#34d399"
                st.markdown(f"<div style='text-align:center;font-weight:700;color:{col};font-size:.9rem;margin-top:8px'>{ca}<br><span style='font-size:.78rem;opacity:.7'>{cds_a:,.1f} pb</span></div>", unsafe_allow_html=True)
            with v2:
                st.markdown('<div class="vs-divider"><div class="vs-line"></div><div class="vs-text">VS</div><div class="vs-line"></div></div>', unsafe_allow_html=True)
            with b2:
                render_flag_small(cb)
                col = "#f87171" if cb!=cn else "#34d399"
                st.markdown(f"<div style='text-align:center;font-weight:700;color:{col};font-size:.9rem;margin-top:8px'>{cb}<br><span style='font-size:.78rem;opacity:.7'>{cds_b:,.1f} pb</span></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _, cb2, _ = st.columns([2, 3, 2])
        with cb2:
            if st.button("🔄 Jugar de nuevo", type="primary", use_container_width=True):
                reset_game(); advance(); st.rerun()

    elif not st.session_state.game_started:
        st.markdown(
            '<div class="welcome-box"><div class="welcome-icon">🎯</div>'
            '<div class="welcome-text">Presiona <b>Iniciar juego</b> para comenzar</div>'
            '<div class="welcome-sub">86 países · Datos reales de CDS · Bloomberg</div>'
            '</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
