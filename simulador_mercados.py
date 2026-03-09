"""
Simulador de Mercados Financieros
==================================
3 juegos educativos:
  1. Simulador de Portafolio de Inversiones
  2. Trading Historico (dia a dia)
  3. Bolsa en Tiempo Real (valoracion por ratios)
"""

import datetime
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ─── Configuracion de pagina ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Simulador de Mercados",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        .metric-card {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 1.2rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin: 0.3rem 0;
        }
        .metric-card h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; }
        .metric-card h2 { margin: 0.3rem 0 0; font-size: 1.6rem; font-weight: 700; }
        .win-banner {
            background: linear-gradient(135deg, #11998e, #38ef7d);
            padding: 1rem; border-radius: 10px; text-align: center;
            font-size: 1.4rem; font-weight: 700; color: white; margin: 1rem 0;
        }
        .lose-banner {
            background: linear-gradient(135deg, #c0392b, #e74c3c);
            padding: 1rem; border-radius: 10px; text-align: center;
            font-size: 1.4rem; font-weight: 700; color: white; margin: 1rem 0;
        }
        .tip-box {
            background: #f0f9ff; border-left: 4px solid #0ea5e9;
            padding: 0.8rem 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Constantes ────────────────────────────────────────────────────────────────
CAPITAL_INICIAL = 100_000.0

ACTIVOS_PORTAFOLIO = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Google (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN",
    "Tesla (TSLA)": "TSLA",
    "Bonos EE.UU. (TLT)": "TLT",
    "Oro (GLD)": "GLD",
    "S&P 500 ETF (SPY)": "SPY",
    "NVIDIA (NVDA)": "NVDA",
    "Meta (META)": "META",
}

ACCIONES_TRADING = {
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Amazon": "AMZN",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
}

ACCIONES_VALORACION = [
    {"simbolo": "AAPL", "nombre": "Apple"},
    {"simbolo": "MSFT", "nombre": "Microsoft"},
    {"simbolo": "GOOGL", "nombre": "Alphabet"},
    {"simbolo": "AMZN", "nombre": "Amazon"},
    {"simbolo": "TSLA", "nombre": "Tesla"},
    {"simbolo": "NVDA", "nombre": "NVIDIA"},
    {"simbolo": "META", "nombre": "Meta"},
    {"simbolo": "JPM",  "nombre": "JPMorgan"},
    {"simbolo": "JNJ",  "nombre": "Johnson & Johnson"},
    {"simbolo": "KO",   "nombre": "Coca-Cola"},
]


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES COMPARTIDAS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def descargar_precios(ticker: str, inicio: str, fin: str) -> pd.Series:
    """Descarga precios de cierre ajustados con yfinance."""
    try:
        df = yf.download(ticker, start=inicio, end=fin, progress=False, auto_adjust=True)
        if df.empty:
            return pd.Series(dtype=float)
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.squeeze()
        return close.dropna()
    except Exception:
        return pd.Series(dtype=float)


def sharpe_ratio(retornos: pd.Series, tasa_libre_riesgo: float = 0.045) -> float:
    """Calcula el Sharpe Ratio anualizado."""
    if retornos.std() == 0:
        return 0.0
    rf_diario = tasa_libre_riesgo / 252
    exceso = retornos - rf_diario
    return float(exceso.mean() / exceso.std() * math.sqrt(252))


def color_retorno(valor: float) -> str:
    if valor > 0:
        return "🟢"
    if valor < 0:
        return "🔴"
    return "⚪"


def formato_pct(valor: float) -> str:
    return f"{'+' if valor >= 0 else ''}{valor:.2f}%"


# ═══════════════════════════════════════════════════════════════════════════════
#  JUEGO 1: SIMULADOR DE PORTAFOLIO
# ═══════════════════════════════════════════════════════════════════════════════

def juego_portafolio():
    st.header("💼 Simulador de Portafolio de Inversiones")
    st.markdown(
        "Distribuye **$100,000 ficticios** entre distintos activos. "
        "El sistema descargará datos reales y mostrará cómo evolucionó tu inversión. "
        "**Gana quien logre el mejor retorno ajustado por riesgo (Sharpe Ratio).**"
    )

    with st.expander("📖 ¿Cómo funciona el Sharpe Ratio?", expanded=False):
        st.markdown(
            """
            El **Sharpe Ratio** mide cuánto retorno extra obtienes por cada unidad de riesgo:

            > **Sharpe = (Retorno portafolio – Tasa libre de riesgo) / Volatilidad**

            - **> 1.0** → Excelente
            - **0.5 – 1.0** → Bueno
            - **< 0.5** → Mejorable
            - **< 0** → El riesgo no fue recompensado
            """
        )

    st.subheader("⚙️ Configuracion")
    col_fecha1, col_fecha2 = st.columns(2)
    fecha_fin_def = datetime.date.today() - datetime.timedelta(days=1)
    fecha_ini_def = fecha_fin_def - datetime.timedelta(days=365)
    with col_fecha1:
        fecha_ini = st.date_input("Fecha de inicio", value=fecha_ini_def,
                                  max_value=fecha_fin_def - datetime.timedelta(days=30),
                                  key="port_fecha_ini")
    with col_fecha2:
        fecha_fin = st.date_input("Fecha de fin", value=fecha_fin_def,
                                  min_value=fecha_ini + datetime.timedelta(days=30),
                                  max_value=fecha_fin_def, key="port_fecha_fin")

    st.subheader("📊 Distribucion del Capital")
    st.info("Ajusta los porcentajes. La suma debe ser exactamente 100%.")

    nombres = list(ACTIVOS_PORTAFOLIO.keys())
    if "port_pesos" not in st.session_state:
        peso_igual = round(100 / len(nombres), 1)
        st.session_state.port_pesos = {n: peso_igual for n in nombres}

    cols = st.columns(2)
    pesos_usuario = {}
    for i, nombre in enumerate(nombres):
        with cols[i % 2]:
            pesos_usuario[nombre] = st.slider(
                nombre,
                min_value=0,
                max_value=100,
                value=int(st.session_state.port_pesos.get(nombre, 10)),
                step=5,
                key=f"slider_{nombre}",
            )

    suma = sum(pesos_usuario.values())
    col_sum, col_btn = st.columns([3, 1])
    with col_sum:
        color = "green" if suma == 100 else "red"
        st.markdown(
            f"**Suma total:** :{color}[{suma}%]  {'✅' if suma == 100 else '❌ Debe ser exactamente 100%'}"
        )
    with col_btn:
        simular = st.button("🚀 Simular Portafolio", type="primary",
                            disabled=(suma != 100), key="btn_simular_port")

    if simular and suma == 100:
        activos_activos = {n: ACTIVOS_PORTAFOLIO[n] for n, p in pesos_usuario.items() if p > 0}
        if not activos_activos:
            st.error("Asigna al menos 1% a algún activo.")
            return

        with st.spinner("Descargando datos de mercado..."):
            precios = {}
            for nombre, ticker in activos_activos.items():
                serie = descargar_precios(ticker, str(fecha_ini), str(fecha_fin))
                if not serie.empty:
                    precios[nombre] = serie

        if not precios:
            st.error("No se pudieron descargar datos. Intenta con otro rango de fechas.")
            return

        # Alinear fechas
        df_precios = pd.DataFrame(precios).dropna()
        if df_precios.empty:
            st.error("No hay datos suficientes para el período seleccionado.")
            return

        # Retornos diarios
        retornos = df_precios.pct_change().dropna()

        # Pesos normalizados solo sobre activos con datos
        pesos_norm = {n: pesos_usuario[n] / 100.0 for n in df_precios.columns}
        vector_pesos = np.array([pesos_norm[n] for n in df_precios.columns])

        # Retorno del portafolio
        retorno_port = retornos.dot(vector_pesos)
        valor_port = CAPITAL_INICIAL * (1 + retorno_port).cumprod()

        # Benchmark: SPY (buy & hold)
        spy = descargar_precios("SPY", str(fecha_ini), str(fecha_fin))
        spy_alineado = spy.reindex(valor_port.index).dropna()
        idx_comun = valor_port.index.intersection(spy_alineado.index)
        spy_norm = spy_alineado[idx_comun] / spy_alineado[idx_comun].iloc[0] * CAPITAL_INICIAL

        st.subheader("📈 Evolución del Portafolio")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=valor_port.index, y=valor_port.values,
            name="Mi Portafolio", line=dict(color="#2563eb", width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=spy_norm.index, y=spy_norm.values,
            name="S&P 500 (benchmark)", line=dict(color="#f59e0b", width=2, dash="dot"),
        ))
        fig.add_hline(y=CAPITAL_INICIAL, line_dash="dash", line_color="gray", opacity=0.5)
        fig.update_layout(
            xaxis_title="Fecha", yaxis_title="Valor del Portafolio (USD)",
            hovermode="x unified", legend=dict(orientation="h", y=1.1),
            height=420, margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Métricas ────────────────────────────────────────────────────────
        valor_final = float(valor_port.iloc[-1])
        retorno_total = (valor_final - CAPITAL_INICIAL) / CAPITAL_INICIAL * 100
        sharpe = sharpe_ratio(retorno_port)
        volatilidad = float(retorno_port.std() * math.sqrt(252) * 100)
        max_dd = _max_drawdown(valor_port)

        spy_ret_total = float(spy_norm.iloc[-1] - CAPITAL_INICIAL) / CAPITAL_INICIAL * 100 if not spy_norm.empty else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            _metric_card("Capital Final", f"${valor_final:,.0f}")
        with m2:
            _metric_card("Retorno Total", formato_pct(retorno_total))
        with m3:
            _metric_card("Sharpe Ratio", f"{sharpe:.3f}")
        with m4:
            _metric_card("Volatilidad Anual", f"{volatilidad:.1f}%")
        with m5:
            _metric_card("Max. Drawdown", f"{max_dd:.1f}%")

        # ── Comparación ──────────────────────────────────────────────────────
        st.subheader("⚔️ Tu Portafolio vs S&P 500")
        diferencia = retorno_total - spy_ret_total
        if diferencia > 0:
            st.markdown(
                f'<div class="win-banner">🏆 ¡Superaste al S&P 500 por {diferencia:.2f}%!</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="lose-banner">📉 El S&P 500 te ganó por {abs(diferencia):.2f}%. '
                f"¡Ajusta tu estrategia!</div>",
                unsafe_allow_html=True,
            )

        # ── Retorno por activo ───────────────────────────────────────────────
        st.subheader("📋 Detalle por Activo")
        rows = []
        for nombre in df_precios.columns:
            ret_act = float((df_precios[nombre].iloc[-1] / df_precios[nombre].iloc[0] - 1) * 100)
            rows.append({
                "Activo": nombre,
                "Peso (%)": int(pesos_usuario[nombre]),
                "Retorno (%)": round(ret_act, 2),
                "Aporte": color_retorno(ret_act) + " " + formato_pct(ret_act),
            })
        df_tabla = pd.DataFrame(rows).sort_values("Retorno (%)", ascending=False)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)

        # Interpretación del Sharpe
        _interpretar_sharpe(sharpe)


def _max_drawdown(serie: pd.Series) -> float:
    pico = serie.cummax()
    dd = (serie - pico) / pico * 100
    return float(dd.min())


def _metric_card(titulo: str, valor: str):
    st.markdown(
        f'<div class="metric-card"><h3>{titulo}</h3><h2>{valor}</h2></div>',
        unsafe_allow_html=True,
    )


def _interpretar_sharpe(sharpe: float):
    if sharpe > 1.5:
        msg = "🥇 Sharpe excelente (>1.5): Excelente compensación riesgo/retorno."
        color = "success"
    elif sharpe > 1.0:
        msg = "✅ Sharpe bueno (1–1.5): Buena gestión del riesgo."
        color = "success"
    elif sharpe > 0.5:
        msg = "⚠️ Sharpe aceptable (0.5–1.0): Retorno moderado dado el riesgo asumido."
        color = "warning"
    elif sharpe > 0:
        msg = "❗ Sharpe bajo (0–0.5): El riesgo apenas se recompensa."
        color = "warning"
    else:
        msg = "🔴 Sharpe negativo: Hubieras obtenido más guardando el dinero en bonos del Tesoro."
        color = "error"
    getattr(st, color)(msg)


# ═══════════════════════════════════════════════════════════════════════════════
#  JUEGO 2: TRADING HISTÓRICO (DÍA A DÍA)
# ═══════════════════════════════════════════════════════════════════════════════

def juego_trading_historico():
    st.header("📉 Trading Histórico — Día a Día")
    st.markdown(
        "Se revela el precio de una acción **día a día** (el futuro está oculto). "
        "Decide cuándo **comprar** y cuándo **vender**. "
        "Al final compara tu rendimiento con la estrategia **Buy & Hold**."
    )

    # ── Inicialización del estado ────────────────────────────────────────────
    if "trad_estado" not in st.session_state:
        _reset_trading()

    estado = st.session_state.trad_estado

    # ── Panel de configuración (solo antes de iniciar) ───────────────────────
    if not estado["iniciado"]:
        st.subheader("⚙️ Configuracion")
        col1, col2, col3 = st.columns(3)
        with col1:
            accion = st.selectbox("Acción", list(ACCIONES_TRADING.keys()), key="trad_accion")
        with col2:
            años = st.slider("Periodo (años)", 1, 5, 2, key="trad_años")
        with col3:
            capital = st.number_input(
                "Capital inicial (USD)", min_value=1000, max_value=1_000_000,
                value=10_000, step=1000, key="trad_capital"
            )

        if st.button("▶ Iniciar Juego", type="primary", key="btn_iniciar_trad"):
            ticker = ACCIONES_TRADING[accion]
            fecha_fin = datetime.date.today() - datetime.timedelta(days=1)
            fecha_ini = fecha_fin - datetime.timedelta(days=365 * años)
            with st.spinner("Descargando datos históricos..."):
                serie = descargar_precios(ticker, str(fecha_ini), str(fecha_fin))
            if serie.empty or len(serie) < 20:
                st.error("No se obtuvieron suficientes datos. Prueba otro período.")
                return
            estado["precios"] = serie.values.tolist()
            estado["fechas"] = [str(d.date()) for d in serie.index]
            estado["capital_ini"] = float(capital)
            estado["efectivo"] = float(capital)
            estado["acciones_en_mano"] = 0.0
            estado["precio_compra"] = 0.0
            estado["dia"] = 0
            estado["historial"] = []
            estado["iniciado"] = True
            estado["terminado"] = False
            estado["nombre_accion"] = accion
            estado["ticker"] = ticker
            st.rerun()
        return

    # ── Juego en curso ────────────────────────────────────────────────────────
    precios = estado["precios"]
    fechas = estado["fechas"]
    dia = estado["dia"]
    total_dias = len(precios)

    precio_actual = precios[dia]
    valor_cartera = estado["efectivo"] + estado["acciones_en_mano"] * precio_actual
    en_posicion = estado["acciones_en_mano"] > 0

    # ── Header de estado ─────────────────────────────────────────────────────
    st.subheader(f"📅 {fechas[dia]}  —  Día {dia + 1} / {total_dias}")
    progress_pct = (dia + 1) / total_dias
    st.progress(progress_pct)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card("Precio Actual", f"${precio_actual:,.2f}")
    with c2:
        _metric_card("Efectivo", f"${estado['efectivo']:,.2f}")
    with c3:
        _metric_card(
            "Acciones en Mano",
            f"{estado['acciones_en_mano']:.4f}" if en_posicion else "—",
        )
    with c4:
        ret_pct = (valor_cartera - estado["capital_ini"]) / estado["capital_ini"] * 100
        _metric_card("Valor Cartera", f"${valor_cartera:,.2f} ({formato_pct(ret_pct)})")

    # ── Gráfico de precios revelados ─────────────────────────────────────────
    precios_visibles = precios[: dia + 1]
    fechas_visibles = fechas[: dia + 1]

    # Marcar operaciones
    compras_x, compras_y, ventas_x, ventas_y = [], [], [], []
    for op in estado["historial"]:
        if op["tipo"] == "COMPRA":
            compras_x.append(op["fecha"])
            compras_y.append(op["precio"])
        else:
            ventas_x.append(op["fecha"])
            ventas_y.append(op["precio"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fechas_visibles, y=precios_visibles,
        name="Precio", line=dict(color="#6366f1", width=2),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.07)",
    ))
    if compras_x:
        fig.add_trace(go.Scatter(
            x=compras_x, y=compras_y, mode="markers",
            marker=dict(symbol="triangle-up", size=14, color="#10b981"),
            name="Compra",
        ))
    if ventas_x:
        fig.add_trace(go.Scatter(
            x=ventas_x, y=ventas_y, mode="markers",
            marker=dict(symbol="triangle-down", size=14, color="#ef4444"),
            name="Venta",
        ))
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Precio (USD)",
        hovermode="x unified", height=360,
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Análisis técnico básico ───────────────────────────────────────────────
    if dia >= 19:
        ventana = min(dia + 1, 20)
        ma20 = sum(precios_visibles[-ventana:]) / ventana
        tendencia = "📈 Alcista" if precio_actual > ma20 else "📉 Bajista"
        st.markdown(
            f'<div class="tip-box">📊 <b>Media Móvil 20 días:</b> ${ma20:,.2f} — '
            f'Tendencia: <b>{tendencia}</b></div>',
            unsafe_allow_html=True,
        )

    # ── Controles de trading ──────────────────────────────────────────────────
    if not estado["terminado"]:
        col_ops = st.columns(4)
        with col_ops[0]:
            pct_comprar = st.selectbox(
                "% del efectivo a invertir", [25, 50, 75, 100], index=3, key="trad_pct_compra"
            )
        with col_ops[1]:
            if st.button("🟢 COMPRAR", type="primary", key="btn_comprar",
                         disabled=en_posicion or estado["efectivo"] < 1):
                monto = estado["efectivo"] * pct_comprar / 100
                estado["acciones_en_mano"] += monto / precio_actual
                estado["efectivo"] -= monto
                estado["precio_compra"] = precio_actual
                estado["historial"].append({
                    "tipo": "COMPRA", "fecha": fechas[dia],
                    "precio": precio_actual, "monto": monto,
                })
                _avanzar_dia(estado, precios, total_dias)
                st.rerun()
        with col_ops[2]:
            if st.button("🔴 VENDER", type="primary", key="btn_vender",
                         disabled=not en_posicion):
                monto_recibido = estado["acciones_en_mano"] * precio_actual
                ganancia = monto_recibido - (estado["acciones_en_mano"] * estado["precio_compra"])
                estado["efectivo"] += monto_recibido
                estado["historial"].append({
                    "tipo": "VENTA", "fecha": fechas[dia],
                    "precio": precio_actual,
                    "ganancia": ganancia,
                })
                estado["acciones_en_mano"] = 0.0
                estado["precio_compra"] = 0.0
                _avanzar_dia(estado, precios, total_dias)
                st.rerun()
        with col_ops[3]:
            if st.button("⏭ SIGUIENTE DÍA", key="btn_siguiente"):
                _avanzar_dia(estado, precios, total_dias)
                st.rerun()

        # Botón saltar al final
        if st.button("⏩ Saltar al Final", key="btn_final"):
            estado["dia"] = total_dias - 1
            estado["terminado"] = True
            st.rerun()

    # ── Historial de operaciones ──────────────────────────────────────────────
    if estado["historial"]:
        with st.expander("📋 Historial de operaciones", expanded=False):
            df_hist = pd.DataFrame(estado["historial"])
            st.dataframe(df_hist, use_container_width=True, hide_index=True)

    # ── Resultados finales ────────────────────────────────────────────────────
    if estado["terminado"] or dia == total_dias - 1:
        _mostrar_resultados_trading(estado, precios, fechas)

    # Botón reiniciar
    if st.button("🔄 Nuevo Juego", key="btn_reset_trad"):
        _reset_trading()
        st.rerun()


def _avanzar_dia(estado: dict, precios: list, total_dias: int):
    if estado["dia"] < total_dias - 1:
        estado["dia"] += 1
    else:
        estado["terminado"] = True


def _mostrar_resultados_trading(estado: dict, precios: list, fechas: list):
    precio_ini = precios[0]
    precio_fin = precios[-1]
    capital_ini = estado["capital_ini"]

    # Liquidar posición abierta al precio final
    valor_final = estado["efectivo"] + estado["acciones_en_mano"] * precio_fin
    retorno_trader = (valor_final - capital_ini) / capital_ini * 100

    # Buy & Hold
    valor_bh = capital_ini * (precio_fin / precio_ini)
    retorno_bh = (valor_bh - capital_ini) / capital_ini * 100

    st.subheader("🏁 Resultados Finales")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🎮 Tu Estrategia")
        st.metric("Capital Final", f"${valor_final:,.2f}",
                  delta=f"{formato_pct(retorno_trader)}")
        st.metric("Operaciones", str(len(estado["historial"])))
    with col2:
        st.markdown("### 📦 Buy & Hold")
        st.metric("Capital Final", f"${valor_bh:,.2f}",
                  delta=f"{formato_pct(retorno_bh)}")

    diferencia = retorno_trader - retorno_bh
    if diferencia > 0:
        st.markdown(
            f'<div class="win-banner">🏆 ¡Superaste Buy & Hold por {diferencia:.2f}%! '
            f"Excelente análisis técnico.</div>",
            unsafe_allow_html=True,
        )
    elif diferencia == 0:
        st.info("Empate exacto con Buy & Hold.")
    else:
        st.markdown(
            f'<div class="lose-banner">📉 Buy & Hold te superó por {abs(diferencia):.2f}%. '
            f"A veces menos es más.</div>",
            unsafe_allow_html=True,
        )

    # Gráfico comparativo final
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Tu Estrategia", "Buy & Hold"],
        y=[retorno_trader, retorno_bh],
        marker_color=["#10b981" if retorno_trader >= retorno_bh else "#ef4444", "#f59e0b"],
        text=[f"{retorno_trader:.2f}%", f"{retorno_bh:.2f}%"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Retorno Total Comparado (%)",
        yaxis_title="Retorno (%)",
        height=350, margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Lección
    st.markdown(
        '<div class="tip-box">💡 <b>Lección clave:</b> Numerosos estudios muestran que más del '
        "80% de los traders activos no superan al índice en el largo plazo. "
        "La clave está en la paciencia y la diversificación.</div>",
        unsafe_allow_html=True,
    )


def _reset_trading():
    st.session_state.trad_estado = {
        "iniciado": False,
        "terminado": False,
        "precios": [],
        "fechas": [],
        "dia": 0,
        "efectivo": 0.0,
        "acciones_en_mano": 0.0,
        "precio_compra": 0.0,
        "capital_ini": 0.0,
        "historial": [],
        "nombre_accion": "",
        "ticker": "",
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  JUEGO 3: VALORACIÓN EN TIEMPO REAL
# ═══════════════════════════════════════════════════════════════════════════════

def juego_valoracion():
    st.header("🔍 Bolsa en Tiempo Real — Valoración por Ratios")
    st.markdown(
        "Descarga cotizaciones reales y clasifica cada acción como "
        "**subvalorada** o **sobrevalorada** usando ratios fundamentales (P/E, P/B, EV/EBITDA)."
    )

    with st.expander("📖 ¿Qué son los ratios de valoración?", expanded=False):
        st.markdown(
            """
| Ratio | Fórmula | Significado | Subvalorada si |
|-------|---------|-------------|----------------|
| **P/E** | Precio / Ganancias por acción | Cuánto pagas por $1 de ganancia | P/E < media del sector |
| **P/B** | Precio / Valor en libros | Cuánto pagas por $1 de activos netos | P/B < 1.5 |
| **EV/EBITDA** | Valor empresa / EBITDA | Valoración total del negocio | EV/EBITDA < 10 |
| **Yield dividendo** | Dividendo / Precio | Renta que recibe el inversor | Yield > 3% |

> **Importante:** Un ratio bajo no siempre significa "comprar". Considera el contexto del sector y el crecimiento futuro.
            """
        )

    if st.button("🔄 Actualizar Datos de Mercado", type="primary", key="btn_actualizar_val"):
        st.cache_data.clear()

    with st.spinner("Descargando datos fundamentales..."):
        datos = _obtener_datos_valoracion()

    if not datos:
        st.error("No se pudieron obtener datos. Verifica tu conexión a Internet.")
        return

    df = pd.DataFrame(datos)

    # ── Tabla interactiva ─────────────────────────────────────────────────────
    st.subheader("📊 Datos Fundamentales en Tiempo Real")

    # Resaltar filas según criterios de valoración
    def _calificar(row):
        puntos = 0
        if pd.notna(row.get("P/E")) and row["P/E"] < 20:
            puntos += 1
        if pd.notna(row.get("P/B")) and row["P/B"] < 3:
            puntos += 1
        if pd.notna(row.get("EV/EBITDA")) and row["EV/EBITDA"] < 12:
            puntos += 1
        if pd.notna(row.get("Yield div. %")) and row["Yield div. %"] > 2:
            puntos += 1
        if puntos >= 3:
            return "🟢 Subvalorada"
        if puntos >= 2:
            return "🟡 Neutral"
        return "🔴 Sobrevalorada"

    df["Valoración"] = df.apply(_calificar, axis=1)

    cols_mostrar = ["Empresa", "Símbolo", "Precio (USD)", "P/E", "P/B",
                    "EV/EBITDA", "Yield div. %", "Mkt Cap (B)", "Valoración"]
    df_display = df[[c for c in cols_mostrar if c in df.columns]].copy()

    st.dataframe(
        df_display.style.applymap(
            lambda v: "color: green; font-weight: bold" if "Subvalorada" in str(v)
            else ("color: #d97706; font-weight: bold" if "Neutral" in str(v)
                  else ("color: red; font-weight: bold" if "Sobrevalorada" in str(v) else "")),
            subset=["Valoración"],
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ── Gráfico de burbujas: P/E vs P/B (tamaño = Mkt Cap) ───────────────────
    st.subheader("🫧 Mapa de Valoración — P/E vs P/B")
    df_grafico = df.dropna(subset=["P/E", "P/B"])
    if not df_grafico.empty:
        mkt_cap = df_grafico.get("Mkt Cap (B)", pd.Series([20] * len(df_grafico)))
        mkt_cap = mkt_cap.fillna(20)

        colores_map = {"🟢 Subvalorada": "#10b981", "🟡 Neutral": "#f59e0b", "🔴 Sobrevalorada": "#ef4444"}
        colores = df_grafico["Valoración"].map(colores_map).fillna("#6366f1")

        fig_bubble = go.Figure()
        for val, color in colores_map.items():
            mask = df_grafico["Valoración"] == val
            sub = df_grafico[mask]
            if sub.empty:
                continue
            fig_bubble.add_trace(go.Scatter(
                x=sub["P/E"], y=sub["P/B"],
                mode="markers+text",
                text=sub["Símbolo"],
                textposition="top center",
                marker=dict(
                    size=(mkt_cap[mask] / mkt_cap.max() * 60 + 15).clip(15, 75),
                    color=color, opacity=0.75,
                    line=dict(width=1, color="white"),
                ),
                name=val,
                hovertemplate=(
                    "<b>%{text}</b><br>P/E: %{x:.1f}<br>P/B: %{y:.1f}<extra></extra>"
                ),
            ))
        fig_bubble.add_vline(x=20, line_dash="dash", line_color="gray", opacity=0.5,
                             annotation_text="P/E = 20")
        fig_bubble.add_hline(y=3, line_dash="dash", line_color="gray", opacity=0.5,
                             annotation_text="P/B = 3")
        fig_bubble.update_layout(
            xaxis_title="P/E Ratio", yaxis_title="P/B Ratio",
            height=460, margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

    # ── Quiz de valoración ───────────────────────────────────────────────────
    st.subheader("🎯 Pon a Prueba tu Análisis")
    st.markdown("Basándote en los datos anteriores, clasifica cada empresa:")

    if "val_respuestas" not in st.session_state:
        st.session_state.val_respuestas = {}
    if "val_enviado" not in st.session_state:
        st.session_state.val_enviado = False

    empresas_quiz = df[["Empresa", "Símbolo", "Valoración"]].head(6)

    for _, row in empresas_quiz.iterrows():
        key = f"quiz_{row['Símbolo']}"
        st.session_state.val_respuestas.setdefault(key, "Neutral")
        opciones = ["Subvalorada", "Neutral", "Sobrevalorada"]
        st.session_state.val_respuestas[key] = st.radio(
            f"**{row['Empresa']} ({row['Símbolo']})**",
            opciones,
            index=opciones.index(st.session_state.val_respuestas[key]),
            horizontal=True,
            key=key + "_radio",
            disabled=st.session_state.val_enviado,
        )

    if not st.session_state.val_enviado:
        if st.button("✅ Evaluar mis Respuestas", type="primary", key="btn_evaluar"):
            st.session_state.val_enviado = True
            st.rerun()
    else:
        correctas = 0
        total = 0
        for _, row in empresas_quiz.iterrows():
            key = f"quiz_{row['Símbolo']}"
            correcta_str = row["Valoración"].replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")
            usuario = st.session_state.val_respuestas.get(key, "")
            total += 1
            if usuario == correcta_str:
                correctas += 1
                st.success(f"✅ {row['Empresa']}: correcto ({correcta_str})")
            else:
                st.error(
                    f"❌ {row['Empresa']}: elegiste **{usuario}**, "
                    f"el modelo dice **{correcta_str}**"
                )

        score_pct = correctas / total * 100 if total else 0
        if score_pct == 100:
            st.markdown(
                '<div class="win-banner">🏆 ¡Perfecto! Dominas el análisis fundamental.</div>',
                unsafe_allow_html=True,
            )
        elif score_pct >= 60:
            st.info(f"🎓 {correctas}/{total} correctas. Buen análisis, sigue practicando.")
        else:
            st.warning(f"📚 {correctas}/{total} correctas. Revisa los ratios y vuelve a intentarlo.")

        if st.button("🔄 Nuevo Quiz", key="btn_reset_quiz"):
            st.session_state.val_respuestas = {}
            st.session_state.val_enviado = False
            st.rerun()


@st.cache_data(ttl=1800, show_spinner=False)
def _obtener_datos_valoracion() -> list:
    """Descarga datos fundamentales para las acciones de valoración."""
    filas = []
    for activo in ACCIONES_VALORACION:
        ticker = activo["simbolo"]
        try:
            info = yf.Ticker(ticker).info
            pe = info.get("trailingPE") or info.get("forwardPE")
            pb = info.get("priceToBook")
            ev_ebitda = info.get("enterpriseToEbitda")
            div_yield = info.get("dividendYield")
            mkt_cap = info.get("marketCap")
            precio = info.get("currentPrice") or info.get("regularMarketPrice")

            filas.append({
                "Empresa": activo["nombre"],
                "Símbolo": ticker,
                "Precio (USD)": round(precio, 2) if precio else None,
                "P/E": round(pe, 1) if pe else None,
                "P/B": round(pb, 2) if pb else None,
                "EV/EBITDA": round(ev_ebitda, 1) if ev_ebitda else None,
                "Yield div. %": round(div_yield * 100, 2) if div_yield else None,
                "Mkt Cap (B)": round(mkt_cap / 1e9, 1) if mkt_cap else None,
            })
        except Exception:
            filas.append({
                "Empresa": activo["nombre"], "Símbolo": ticker,
                "Precio (USD)": None, "P/E": None, "P/B": None,
                "EV/EBITDA": None, "Yield div. %": None, "Mkt Cap (B)": None,
            })
    return filas


# ═══════════════════════════════════════════════════════════════════════════════
#  NAVEGACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/"
            "NYSE_MKT_at_Broad_St_and_Wall_St_jeh.jpg/320px-NYSE_MKT_at_Broad_St_and_Wall_St_jeh.jpg",
            use_container_width=True,
        )
        st.title("📈 Simulador de Mercados")
        st.caption("Aprende finanzas con datos reales")
        st.divider()

        juego = st.radio(
            "Selecciona un juego:",
            [
                "💼 Portafolio de Inversiones",
                "📉 Trading Histórico",
                "🔍 Valoración en Tiempo Real",
            ],
            key="juego_seleccionado",
        )
        st.divider()
        st.caption(
            "Datos provistos por **Yahoo Finance** via yfinance.  \n"
            "Solo con fines educativos — no constituye asesoría financiera."
        )

    if juego == "💼 Portafolio de Inversiones":
        juego_portafolio()
    elif juego == "📉 Trading Histórico":
        juego_trading_historico()
    else:
        juego_valoracion()


if __name__ == "__main__":
    main()
