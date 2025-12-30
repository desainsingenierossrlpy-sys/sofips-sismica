import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os 
import base64 
from ui.map_selector import mostrar_mapa_selector
from core.norma_e030 import NormaE030

# 1. Configuración de la página
st.set_page_config(page_title="SOFIPS | Ingeniería Sísmica", layout="wide", page_icon="🏗️")

# --- CSS GLOBAL: CURSOR ---
st.markdown("""
<style>
.st-emotion-cache-16cqk79, .leaflet-container, .leaflet-grab, .leaflet-interactive { cursor: crosshair !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER (LOGO + TÍTULO) ---
c_logo, c_text = st.columns([0.25, 0.75]) 
with c_logo:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<img src="data:image/png;base64,{img_base64}" style="width: 260px; max-width: 100%;">', unsafe_allow_html=True)

with c_text:
    st.markdown("""
        <div style="display: flex; flex-direction: column; justify-content: center; height: 120px;">
            <h3 style="margin: 0; color: #2C3E50; font-weight: bold; font-size: 28px; line-height: 1.2;">SOFIPS: Software informático de análisis y diseño sismorresistente</h3>
            <p style="margin: 8px 0 0 0; color: gray; font-size: 16px;">Desarrollo: <b>Ing. Arnold Mendo Rodriguez</b> | Norma Peruana E.030 (2025)</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- LAYOUT PRINCIPAL ---
col_izq, col_der = st.columns([1, 1.3], gap="large")

# COLUMNA IZQUIERDA: MAPA
with col_izq:
    lat, lon, direccion, depto = mostrar_mapa_selector()
    if lat:
        st.success(f"📍 **Ubicación:** {direccion}")
        
        # Automatización de Zonas
        MAPPING_ZONAS = {
            'TUMBES': 4, 'PIURA': 4, 'LAMBAYEQUE': 4, 'LA LIBERTAD': 4, 'ANCASH': 4, 
            'LIMA': 4, 'CALLAO': 4, 'ICA': 4, 'AREQUIPA': 4, 'MOQUEGUA': 4, 'TACNA': 4,
            'CAJAMARCA': 3, 'SAN MARTIN': 3, 'HUANCAVELICA': 3, 'AYACUCHO': 3, 
            'APURIMAC': 3, 'PASCO': 3, 'JUNIN': 3,
            'AMAZONAS': 2, 'HUANUCO': 2, 'UCAYALI': 2, 'CUSCO': 2, 'PUNO': 2,
            'LORETO': 1, 'MADRE DE DIOS': 1
        }
        if depto:
            if "last_depto" not in st.session_state or st.session_state["last_depto"] != depto:
                st.session_state["last_depto"] = depto
                st.session_state["zona_seleccionada"] = MAPPING_ZONAS.get(depto, 4)
                st.rerun()

# COLUMNA DERECHA: DATOS
with col_der:
    st.subheader("⚙️ Parámetros de Diseño")
    
    # Fila 1
    c1, c2, c3 = st.columns(3)
    if "zona_seleccionada" not in st.session_state: st.session_state["zona_seleccionada"] = 4
    zona = c1.selectbox("Zona (Z)", [4, 3, 2, 1], key="zona_seleccionada")
    suelo = c2.selectbox("Suelo (S)", ["S0", "S1", "S2", "S3"], index=1)
    cat = c3.selectbox("Uso (U)", ["A1", "A2", "B", "C"], index=2)

    # Fila 2
    c4, c5 = st.columns(2)
    rx = c4.number_input("R Coeficiente (Dir X)", value=8.0, step=0.5)
    ry = c5.number_input("R Coeficiente (Dir Y)", value=6.0, step=0.5)

    # Fila 3: UNIDADES (MEJORA)
    st.write("📏 **Unidades de Salida**")
    unidad = st.radio("Seleccione unidad para Gráfica y Tablas:", ["g (Fracción de Gravedad)", "m/s²"], horizontal=True)
    factor_g = 9.81 if unidad == "m/s²" else 1.0
    label_eje = "Aceleración (m/s²)" if unidad == "m/s²" else "Aceleración (g)"

    ejecutar = st.button("🚀 Calcular Espectros Combinados", type="primary", use_container_width=True)

    if ejecutar:
        norma = NormaE030()
        
        # 1. Obtener datos crudos (en g)
        Tx, Sa_x_des_raw, Sa_el_raw, info = norma.get_spectrum_curve({'zona': zona, 'suelo': suelo, 'categoria': cat, 'R_coef': rx})
        _, Sa_y_des_raw, _, _ = norma.get_spectrum_curve({'zona': zona, 'suelo': suelo, 'categoria': cat, 'R_coef': ry})

        # 2. Convertir unidades
        Sa_el = Sa_el_raw * factor_g
        Sa_x_des = Sa_x_des_raw * factor_g
        Sa_y_des = Sa_y_des_raw * factor_g

        # 3. Mostrar Resumen de Parámetros (MEJORA)
        st.markdown("### 📝 Resumen de Parámetros (E.030)")
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Factor Z", f"{info['Z']}g")
        p2.metric("Factor U", f"{info['U']}")
        p3.metric("Factor S", f"{info['S']}")
        p4.metric("TP", f"{info['TP']} s")
        p5.metric("TL", f"{info['TL']} s")

        # 4. Gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Tx, y=Sa_el, mode='lines', line=dict(color='red', width=2, dash='dash'), name='Espectro Elástico (R=1)'))
        fig.add_trace(go.Scatter(x=Tx, y=Sa_x_des, mode='lines', fill='tonexty', fillcolor='rgba(255, 0, 0, 0.15)', line=dict(color='black', width=3), name=f'Diseño X-X (R={rx})'))
        fig.add_trace(go.Scatter(x=Tx, y=Sa_y_des, mode='lines', line=dict(color='blue', width=2), name=f'Diseño Y-Y (R={ry})'))

        fig.update_layout(
            title=dict(text=f"<b>ESPECTRO E.030 ({label_eje})</b>", font=dict(size=16)),
            xaxis=dict(title="Periodo T (s)", showgrid=True, gridcolor='lightgray'),
            yaxis=dict(title=label_eje, showgrid=True, gridcolor='lightgray'),
            template="plotly_white", height=500, hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # 5. Tablas y Descargas
        with st.expander("📋 Ver Tabla de Datos y Descargar"):
            df = pd.DataFrame({
                "T (s)": Tx,
                f"Sa Elástico ({unidad})": Sa_el,
                f"Sa Diseño X ({unidad})": Sa_x_des,
                f"Sa Diseño Y ({unidad})": Sa_y_des
            })
            st.dataframe(df, use_container_width=True)
            
            # Descargas TXT
            txt_x = df.iloc[:, [0, 2]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
            txt_y = df.iloc[:, [0, 3]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
            
            d1, d2 = st.columns(2)
            d1.download_button(f"📥 TXT ETABS Dir X ({unidad})", txt_x, f"Espectro_X_{unidad}.txt", "text/plain")
            d2.download_button(f"📥 TXT ETABS Dir Y ({unidad})", txt_y, f"Espectro_Y_{unidad}.txt", "text/plain")