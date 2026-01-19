import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import os
import base64
from ui.map_selector import mostrar_mapa_selector
from core.location_data import LocationData
from core.norma_e030 import NormaE030
from ui.pdf_report import create_pdf

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="SOFIPS | Suite Sísmica v2025", layout="wide", page_icon="🏗️")

# --- INICIALIZACIÓN ---
if "loc_data" not in st.session_state:
    st.session_state.loc_data = LocationData()
if "zona_key" not in st.session_state:
    st.session_state.zona_key = 4
if "calculo_realizado" not in st.session_state:
    st.session_state.calculo_realizado = False

norma = NormaE030()

# Parche técnico para periodos de suelo
if not hasattr(norma, 'periodos_suelo'):
    norma.periodos_suelo = {
        'S0':{'Tp':0.3, 'Tl':3.0}, 'S1':{'Tp':0.4, 'Tl':3.0},
        'S2':{'Tp':0.6, 'Tl':2.0}, 'S3':{'Tp':1.0, 'Tl':1.6}, 'S4':{'Tp':1.0, 'Tl':1.6}
    }

# --- SIDEBAR ---
with st.sidebar:
    # 2.0 COLOCAR LOGO DESAINS
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=250) # Tamaño razonable
    else:
        st.title("🏗️ SOFIPS v2025")
    
    st.subheader("🎨 Estilo Visual")
    tipo_fuente = st.selectbox("Fuente Reporte PDF", ["Helvetica", "Courier", "Times"])
    fs = st.slider("Tamaño de Texto Interfaz (px)", 14, 26, 18)
    
    # --- BLOQUE CSS MEJORADO (TABLAS Y MÉTRICAS) ---
    st.markdown(f"""
        <style>
        /* Encabezados y Texto General */
        h1 {{ font-size: {fs + 14}px !important; }}
        p, span, label {{ font-size: {fs}px !important; }}
        
        /* METRICAS SUPERIORES (Z, U, S, Tp, Tl) */
        [data-testid="stMetricLabel"] p {{
            font-size: {fs + 2}px !important;
            font-weight: bold !important;
            color: #2C3E50 !important;
        }}
        [data-testid="stMetricValue"] div {{
            font-size: {fs + 22}px !important;
            font-weight: 900 !important;
            color: #1E40AF !important; /* Azul intenso */
        }}

        /* TABLA DE RESULTADOS (Números más grandes) */
        .stDataFrame div[data-testid="stTable"] {{
            font-size: {fs + 4}px !important;
        }}
        .stDataFrame td, .stDataFrame th {{
            font-size: {fs + 4}px !important; /* Números un poco más grandes que el texto */
            padding: 10px !important;
        }}

        /* PESTAÑAS (Tabs) */
        button[data-baseweb="tab"] p {{
            font-size: {fs + 4}px !important;
            font-weight: bold !important;
        }}
        
        /* Botón de calcular */
        .stButton button {{
            height: 3em !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("---")
    unidad_acel = st.radio("Unidades:", ["g", "m/s²"], horizontal=True)
    factor_g = 9.81 if unidad_acel == "m/s²" else 1.0

    st.subheader("⚙️ Parámetros E.030")
    zona_sel = st.selectbox("Zona (Z)", [4, 3, 2, 1], index=[4, 3, 2, 1].index(st.session_state.zona_key))
    suelo_sel = st.selectbox("Suelo (S)", list(norma.factor_S.keys()))
    u_val = st.number_input("Uso (U)", value=1.0, step=0.1)

    st.subheader("🏗️ Coeficientes R")
    tx, ty = st.tabs(["Dir X", "Dir Y"])
    with tx: rx = st.number_input("R X", value=8.0)
    with ty: ry = st.number_input("R Y", value=8.0)
    
    if st.button("🚀 Calcular Espectro", type="primary", use_container_width=True):
        st.session_state.calculo_realizado = True
        st.session_state.zona_key = zona_sel

# --- ÁREA PRINCIPAL ---
st.header("Análisis y Diseño Sismorresistente - Perú")

if st.session_state.calculo_realizado:
    S_val = norma.factor_S[suelo_sel][zona_sel]
    Tp, Tl = norma.periodos_suelo[suelo_sel]['Tp'], norma.periodos_suelo[suelo_sel]['Tl']
    Z_val = {4:0.45, 3:0.35, 2:0.25, 1:0.10}[zona_sel]
    
    m_cols = st.columns(5)
    m_cols[0].metric("Zona (Z)", f"{Z_val}g")
    m_cols[1].metric("Uso (U)", f"{u_val}")
    m_cols[2].metric("Suelo (S)", f"{S_val}")
    m_cols[3].metric("Tp", f"{Tp} s")
    m_cols[4].metric("Tl", f"{Tl} s")

tab1, tab2, tab3 = st.tabs(["📍 Ubicación", "📊 Espectro", "💾 Exportar Datos"])

with tab1:
    col_sel, col_map = st.columns([1, 2.5])
    with col_sel:
        st.subheader("Selección de Lugar")
        deptos = st.session_state.loc_data.get_departamentos()
        depto = st.selectbox("Departamento", deptos, index=deptos.index("LIMA") if "LIMA" in deptos else 0)
        provs = st.session_state.loc_data.get_provincias(depto)
        prov = st.selectbox("Provincia", provs, index=0)
        df_dist = st.session_state.loc_data.get_distritos_data(prov)
        dist_name = st.selectbox("Distrito", df_dist['Distrito'].tolist())
        row = df_dist[df_dist['Distrito'] == dist_name].iloc[0]
        
        if st.session_state.zona_key != int(row['Zona sismica']):
            st.session_state.zona_key = int(row['Zona sismica']); st.rerun()
            
        st.info(f"DISTRITO: {dist_name} | ZONA: {row['Zona sismica']}")
    with col_map:
        lat, lon = mostrar_mapa_selector(force_center=[row['Latitud'], row['Longitud']])

with tab2:
    if st.session_state.calculo_realizado:
        T = np.arange(0, 6.02, 0.02)
        Sa_E, Sa_X, Sa_Y = [], [], []
        for t in T:
            if t < 0.2*Tp: C = 1 + 7.5*(t/Tp)
            elif t <= Tp: C = 2.5
            elif t <= Tl: C = 2.5*(Tp/t)
            else: C = 2.5*(Tp*Tl/(t**2))
            base = (Z_val * u_val * C * S_val) * factor_g
            Sa_E.append(base); Sa_X.append(base/rx); Sa_Y.append(base/ry)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=T, y=Sa_X, name="Diseño X", line=dict(color='black', width=4)))
        fig.add_trace(go.Scatter(x=T, y=Sa_Y, name="Diseño Y", line=dict(color='blue', width=2, dash='dot')))
        fig.add_trace(go.Scatter(x=T, y=Sa_E, name="Elástico", line=dict(color='red', dash='dash'),
                                 fill='tonexty', fillcolor='rgba(255, 0, 0, 0.15)'))
        
        fig.update_layout(template="plotly_white", height=800, xaxis_title="Periodo T (s)", yaxis_title=f"Sa ({unidad_acel})")
        st.plotly_chart(fig, use_container_width=True)
        
        st.session_state.df_final = pd.DataFrame({"T(s)":T, "Sa_Elastic":Sa_E, "Sa_X":Sa_X, "Sa_Y":Sa_Y})

        if st.button("📄 Generar Memoria PDF", type="primary"):
            img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
            pdf_data = create_pdf({'rx':rx, 'ry':ry, 'Z':Z_val, 'U':u_val, 'S':S_val},
                                   {'Tp':Tp, 'Tl':Tl, 'distrito':dist_name},
                                   f"{lat:.5f}, {lon:.5f}", st.session_state.df_final, 
                                   io.BytesIO(img_bytes), tipo_fuente, fs)
            st.download_button("📥 Descargar Reporte", pdf_data, "Memoria_E030.pdf", mime="application/pdf")

with tab3:
    if "df_final" in st.session_state:
        st.subheader("Tabla de Resultados (Paso: 0.02s)")
        st.dataframe(st.session_state.df_final, use_container_width=True, height=600)
        
        c1, c2 = st.columns(2)
        for i, col in enumerate(["Sa_X", "Sa_Y"]):
            buff = io.StringIO()
            for _, r in st.session_state.df_final.iterrows():
                buff.write(f"{r['T(s)']:.4f}\t{r[col]:.6f}\n")
            [c1, c2][i].download_button(f"📥 Exportar TXT {col}", buff.getvalue(), f"Espectro_{col}.txt")