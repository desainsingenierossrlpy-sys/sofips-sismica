import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os 
import base64 
from ui.map_selector import mostrar_mapa_selector
from core.norma_e030 import NormaE030

# 1. Configuración de la página
st.set_page_config(page_title="SOFIPS | Ingeniería Sísmica", layout="wide", page_icon="🏗️")

# --- 2. HEADER UNIFICADO (HTML FLEXBOX) ---
# Esto garantiza que el logo y el texto estén pegados y alineados
logo_path = "assets/logo.png"

if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    
    # HTML AVANZADO:
    # - width: 320px (Logo más grande)
    # - margin-right: 15px (Distancia corta entre logo y texto)
    header_html = f"""
    <div style="display: flex; align-items: center; background-color: white; padding: 10px; border-radius: 10px;">
        <img src="data:image/png;base64,{img_base64}" style="width: 320px; object-fit: contain; margin-right: 15px;">
        <div>
            <h2 style="margin: 0; color: #2C3E50; font-weight: 800; font-size: 32px; letter-spacing: -1px;">
                SOFIPS: Software informático de análisis y diseño sismorresistente
            </h2>
            <p style="margin: 5px 0 0 0; color: #555; font-size: 18px;">
                Desarrollo: <b>Ing. Arnold Mendo Rodriguez</b> | Norma Peruana E.030 (2025)
            </p>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
else:
    st.error("⚠️ Error: No se encuentra assets/logo.png")

st.markdown("---")

# --- 3. LAYOUT PRINCIPAL ---
col_izq, col_der = st.columns([1, 1.3], gap="large")

# COLUMNA IZQUIERDA: MAPA
with col_izq:
    lat, lon, direccion, depto = mostrar_mapa_selector()
    if lat:
        st.success(f"📍 **Ubicación:** {direccion}")
        
        # --- CEREBRO: DETECCIÓN AUTOMÁTICA ---
        if depto:
            # MAPPING E.030 (Departamentos -> Zonas)
            MAPPING_ZONAS = {
                'TUMBES': 4, 'PIURA': 4, 'LAMBAYEQUE': 4, 'LA LIBERTAD': 4, 'ANCASH': 4, 
                'LIMA': 4, 'CALLAO': 4, 'ICA': 4, 'AREQUIPA': 4, 'MOQUEGUA': 4, 'TACNA': 4,
                'CAJAMARCA': 3, 'SAN MARTIN': 3, 'HUANCAVELICA': 3, 'AYACUCHO': 3, 
                'APURIMAC': 3, 'PASCO': 3, 'JUNIN': 3,
                'AMAZONAS': 2, 'HUANUCO': 2, 'UCAYALI': 2, 'CUSCO': 2, 'PUNO': 2,
                'LORETO': 1, 'MADRE DE DIOS': 1
            }
            
            if "last_depto" not in st.session_state or st.session_state["last_depto"] != depto:
                st.session_state["last_depto"] = depto
                zona_sugerida = MAPPING_ZONAS.get(depto, 4)
                st.session_state["zona_seleccionada"] = zona_sugerida
                st.toast(f"🌍 Zona {zona_sugerida} detectada ({depto})", icon="✅")
                st.rerun()

# COLUMNA DERECHA: DATOS
with col_der:
    st.subheader("⚙️ Parámetros de Diseño")
    
    c1, c2, c3 = st.columns(3)
    if "zona_seleccionada" not in st.session_state: st.session_state["zona_seleccionada"] = 4
    
    zona = c1.selectbox("Zona (Z)", [4, 3, 2, 1], key="zona_seleccionada")
    suelo = c2.selectbox("Suelo (S)", ["S0", "S1", "S2", "S3"], index=1)
    cat = c3.selectbox("Uso (U)", ["A1", "A2", "B", "C"], index=2)

    c4, c5 = st.columns(2)
    rx = c4.number_input("R Coeficiente (Dir X)", value=8.0, step=0.5)
    ry = c5.number_input("R Coeficiente (Dir Y)", value=6.0, step=0.5)

    ejecutar = st.button("🚀 Calcular Espectros Combinados", type="primary", use_container_width=True)

    if ejecutar:
        norma = NormaE030()
        Tx, Sa_x_des, Sa_el, info = norma.get_spectrum_curve({'zona': zona, 'suelo': suelo, 'categoria': cat, 'R_coef': rx})
        _, Sa_y_des, _, _ = norma.get_spectrum_curve({'zona': zona, 'suelo': suelo, 'categoria': cat, 'R_coef': ry})

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Tx, y=Sa_el, mode='lines', line=dict(color='red', width=2, dash='dash'), name='Espectro Elástico (R=1)'))
        fig.add_trace(go.Scatter(x=Tx, y=Sa_x_des, mode='lines', fill='tonexty', fillcolor='rgba(255, 0, 0, 0.15)', line=dict(color='black', width=3), name=f'Diseño X-X (R={rx})'))
        fig.add_trace(go.Scatter(x=Tx, y=Sa_y_des, mode='lines', line=dict(color='blue', width=2), name=f'Diseño Y-Y (R={ry})'))

        fig.update_layout(
            title=dict(text=f"<b>ESPECTRO E.030 COMBINADO</b> (Z{info['Z']} S{info['S']} TP={info['TP']})", font=dict(size=16)),
            xaxis=dict(title="Periodo T (s)", showgrid=True, gridcolor='lightgray'),
            yaxis=dict(title="Aceleración Sa (m/s²)", showgrid=True, gridcolor='lightgray'),
            template="plotly_white", height=500, hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Ver Tabla de Datos Numéricos"):
            df = pd.DataFrame({"T (s)": Tx, "Sa Elástico": Sa_el, "Sa Diseño X": Sa_x_des, "Sa Diseño Y": Sa_y_des})
            st.dataframe(df, use_container_width=True)
            txt_x = df[['T (s)', 'Sa Diseño X']].to_csv(sep='\t', index=False, header=False).encode('utf-8')
            st.download_button("📥 Descargar TXT ETABS (Dir X)", txt_x, "Espectro_X.txt", "text/plain")