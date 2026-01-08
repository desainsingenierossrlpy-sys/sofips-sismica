import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os 
import base64 
import io
from ui.map_selector import mostrar_mapa_selector
from core.seismic_manager import SeismicManager # <--- NUEVO GESTOR
from ui.pdf_report import create_pdf

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SOFIPS | Suite Sísmica", layout="wide", page_icon="🏗️")

# CSS Global (Cursor y Estilos)
st.markdown("""
<style>
.st-emotion-cache-16cqk79, .leaflet-container, .leaflet-grab, .leaflet-interactive, .leaflet-dragging .leaflet-grab {
    cursor: crosshair !important;
}
.custom-metric { background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 5px; padding: 8px; text-align: center; margin-bottom: 10px; }
.metric-label { font-size: 12px; color: #666; margin: 0; text-transform: uppercase; font-weight: 600; }
.metric-value { font-size: 18px; font-weight: bold; color: #2C3E50; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BARRA LATERAL (NAVEGACIÓN)
# ---------------------------------------------------------
with st.sidebar:
    # Logo
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    st.title("🎛️ Panel de Control")
    st.markdown("---")
    
    # 1. Selector de País
    manager = SeismicManager()
    pais_seleccionado = st.selectbox("📍 Normativa / País", list(manager.available_codes.keys()))
    
    # 2. Selector de Módulo
    st.markdown("### 🛠️ Módulos")
    modulo = st.radio("Seleccione herramienta:", 
                      ["Espectro de Diseño", "Verificación E.030 (ETABS)"])
    
    st.info("v1.5 Enterprise Cloud")

# ---------------------------------------------------------
# ÁREA PRINCIPAL
# ---------------------------------------------------------

# Header Dinámico
st.markdown(f"""
    <div style="padding-bottom: 10px;">
        <h2 style="color: #2C3E50; margin-bottom: 0;">SOFIPS: {pais_seleccionado.split('(')[0]}</h2>
        <p style="color: gray; font-size: 18px;">Módulo Activo: <b>{modulo}</b></p>
    </div>
    <hr style="margin-top: 0;">
""", unsafe_allow_html=True)


# === LÓGICA: MÓDULO DE ESPECTRO ===
if modulo == "Espectro de Diseño":
    
    NormaClass = manager.get_norma_class(pais_seleccionado)
    
    # CASO 1: PERÚ (El único implementado al 100%)
    if NormaClass and "Perú" in pais_seleccionado:
        col_izq, col_der = st.columns([1, 1.3], gap="large")

        # --- IZQUIERDA: MAPA ---
        with col_izq:
            lat, lon, direccion, depto = mostrar_mapa_selector()
            if lat:
                st.success(f"📍 **Ubicación:** {direccion}")
                # Automatización de Zonas (Perú)
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

        # --- DERECHA: CÁLCULOS ---
        with col_der:
            norma = NormaClass() # Instancia la clase NormaE030
            st.subheader("⚙️ Parámetros de Diseño")
            
            c1, c2, c3 = st.columns(3)
            if "zona_seleccionada" not in st.session_state: st.session_state["zona_seleccionada"] = 4
            
            zona = c1.selectbox("Zona (Z)", [4, 3, 2, 1], key="zona_seleccionada")
            suelo = c2.selectbox("Suelo (S)", ["S0", "S1", "S2", "S3", "S4"], index=1)
            cat = c3.selectbox("Uso (U)", ["A1", "A2", "B", "C"], index=2)

            c4, c5 = st.columns(2)
            rx = c4.number_input("R Coeficiente (Dir X)", value=8.0, step=0.5)
            ry = c5.number_input("R Coeficiente (Dir Y)", value=6.0, step=0.5)

            st.write("📏 **Unidades**")
            unidad = st.radio("Output:", ["g", "m/s²"], horizontal=True, label_visibility="collapsed")
            factor_g = 9.81 if unidad == "m/s²" else 1.0
            label_eje = "Aceleración (m/s²)" if unidad == "m/s²" else "Aceleración (g)"

            ejecutar = st.button("🚀 Calcular Espectros", type="primary", use_container_width=True)

            if ejecutar:
                Tx, Sa_x_des_raw, Sa_el_raw, info = norma.get_spectrum_curve({'zona': zona, 'suelo': suelo, 'categoria': cat, 'R_coef': rx})
                _, Sa_y_des_raw, _, _ = norma.get_spectrum_curve({'zona': zona, 'suelo': suelo, 'categoria': cat, 'R_coef': ry})

                if info.get('Error'):
                    st.error(info['Error'])
                else:
                    # Conversión de unidades
                    Sa_el = Sa_el_raw * factor_g
                    Sa_x_des = Sa_x_des_raw * factor_g
                    Sa_y_des = Sa_y_des_raw * factor_g

                    # Panel de Parámetros
                    st.markdown("### 📝 Parámetros")
                    p1, p2, p3, p4, p5 = st.columns(5)
                    p1.markdown(f'<div class="custom-metric"><p class="metric-label">Z</p><p class="metric-value">{info["Z"]}g</p></div>', unsafe_allow_html=True)
                    p2.markdown(f'<div class="custom-metric"><p class="metric-label">U</p><p class="metric-value">{info["U"]}</p></div>', unsafe_allow_html=True)
                    p3.markdown(f'<div class="custom-metric"><p class="metric-label">S</p><p class="metric-value">{info["S"]}</p></div>', unsafe_allow_html=True)
                    p4.markdown(f'<div class="custom-metric"><p class="metric-label">TP</p><p class="metric-value">{info["TP"]}s</p></div>', unsafe_allow_html=True)
                    p5.markdown(f'<div class="custom-metric"><p class="metric-label">TL</p><p class="metric-value">{info["TL"]}s</p></div>', unsafe_allow_html=True)

                    # Gráfico
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=Tx, y=Sa_el, mode='lines', line=dict(color='red', width=2, dash='dash'), name='Elástico (R=1)'))
                    fig.add_trace(go.Scatter(x=Tx, y=Sa_x_des, mode='lines', fill='tonexty', fillcolor='rgba(255, 0, 0, 0.15)', line=dict(color='black', width=3), name=f'Diseño X (R={rx})'))
                    fig.add_trace(go.Scatter(x=Tx, y=Sa_y_des, mode='lines', line=dict(color='blue', width=2), name=f'Diseño Y (R={ry})'))

                    fig.update_layout(
                        title=dict(text=f"<b>ESPECTRO {label_eje}</b>", font=dict(size=14)),
                        xaxis=dict(title="Periodo T (s)", showgrid=True, gridcolor='lightgray'),
                        yaxis=dict(title=label_eje, showgrid=True, gridcolor='lightgray'),
                        template="plotly_white", height=450, hovermode="x unified",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Exportación y PDF
                    with st.expander("📋 Descargas (PDF / Excel / ETABS)", expanded=True):
                        df = pd.DataFrame({
                            "T (s)": Tx,
                            f"Sa Elástico ({unidad})": Sa_el,
                            f"Sa Diseño X ({unidad})": Sa_x_des,
                            f"Sa Diseño Y ({unidad})": Sa_y_des
                        })
                        st.dataframe(df, use_container_width=True, height=200)
                        
                        col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
                        
                        # TXT ETABS
                        txt_x = df.iloc[:, [0, 2]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                        txt_y = df.iloc[:, [0, 3]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                        
                        col_d1.download_button(f"📥 ETABS Dir X", txt_x, f"Espectro_X.txt", "text/plain")
                        col_d2.download_button(f"📥 ETABS Dir Y", txt_y, f"Espectro_Y.txt", "text/plain")
                        
                        # PDF
                        img_bytes = fig.to_image(format="png", width=800, height=400, scale=2)
                        img_stream = io.BytesIO(img_bytes)
                        report_params = {'suelo': suelo, 'categoria': cat, 'rx': rx, 'ry': ry, 'unidad': unidad, 'direccion': direccion}
                        pdf_bytes = create_pdf(report_params, info, direccion, df, img_stream)
                        col_d3.download_button("📄 Reporte PDF", pdf_bytes, "Memoria_SOFIPS.pdf", "application/pdf", type="primary")

    # CASO 2: OTROS PAÍSES (Placeholder)
    else:
        st.warning(f"⚠️ El módulo para **{pais_seleccionado}** está en desarrollo. Próximamente disponible.")
        st.image("https://media.giphy.com/media/l2JHVUriDGEtWOx0c/giphy.gif", width=300)


# === LÓGICA: MÓDULO DE VERIFICACIÓN ETABS (NUEVO) ===
elif modulo == "Verificación E.030 (ETABS)":
    
    st.info("ℹ️ Este módulo permite auditar automáticamente los resultados de ETABS según la Norma E.030.")
    
    col_up, col_info = st.columns([1, 1])
    
    with col_up:
        st.markdown("### 📂 Cargar Resultados de ETABS")
        st.markdown("Por favor, exporte las tablas **'Story Drifts'** y **'Base Reactions'** a Excel y súbalas aquí.")
        
        uploaded_file = st.file_uploader("Arrastra tu archivo Excel (.xlsx)", type=["xlsx"])
        
        if uploaded_file:
            st.success("✅ Archivo recibido. Analizando estructura...")
            st.progress(25)
            # AQUÍ EN EL FUTURO PROGRAMAREMOS LA LECTURA DE PANDAS
            st.warning("🚧 El motor de verificación está en construcción. (Fase 4)")
            
    with col_info:
        st.markdown("### ¿Qué verifica este módulo?")
        st.markdown("""
        - [ ] **Cortante Mínimo:** Verifica si $V_{din} \ge 0.8 V_{est}$ (Regular) o $0.9 V_{est}$ (Irregular).
        - [ ] **Derivas (Drifts):** Compara contra los límites (0.007 Concreto, 0.010 Acero).
        - [ ] **Irregularidades:** Detecta piso blando o torsión (si se suben datos modales).
        - [ ] **Participación de Masa:** Verifica que supere el 90%.
        """)
        st.metric("Estado del Módulo", "En Desarrollo", delta="Próximamente", delta_color="off")