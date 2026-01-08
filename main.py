import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os 
import base64 
import io
from ui.map_selector import mostrar_mapa_selector
from core.seismic_manager import SeismicManager
from ui.pdf_report import create_pdf
from core.etabs_validator import EtabsValidator

st.set_page_config(page_title="SOFIPS | Suite Sísmica", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
.st-emotion-cache-16cqk79, .leaflet-container, .leaflet-grab, .leaflet-interactive { cursor: crosshair !important; }
.custom-metric { background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 5px; padding: 8px; text-align: center; margin-bottom: 10px; }
.metric-label { font-size: 12px; color: #666; margin: 0; text-transform: uppercase; font-weight: 600; }
.metric-value { font-size: 18px; font-weight: bold; color: #2C3E50; margin: 0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.title("🎛️ Panel de Control")
    st.markdown("---")
    manager = SeismicManager()
    pais_seleccionado = st.selectbox("📍 Normativa / País", list(manager.available_codes.keys()))
    st.markdown("### 🛠️ Herramientas")
    modulo = st.radio("Seleccione módulo:", ["Espectro de Diseño", "Verificación E.030 (ETABS)"])
    st.info("v2.1 Enterprise Cloud")

# HEADER
logo_header = "assets/logo.png"
if os.path.exists(logo_header):
    with open(logo_header, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    header_html = f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{img_base64}" style="width: 260px; max-width: 100%; margin-right: 20px;">
        <div>
            <h3 style="margin: 0; color: #2C3E50; font-weight: bold; font-size: 28px; line-height: 1.2;">SOFIPS: Software informático de análisis y diseño sismorresistente</h3>
            <p style="margin: 5px 0 0 0; color: gray; font-size: 16px;">Módulo Activo: <b>{modulo}</b> | Norma Peruana E.030 (2025)</p>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    st.markdown("---")

if modulo == "Espectro de Diseño":
    NormaClass = manager.get_norma_class(pais_seleccionado)
    if NormaClass and "Perú" in pais_seleccionado:
        norma = NormaClass() # Instancia para acceder a las listas
        
        col_izq, col_der = st.columns([1, 1.4], gap="large")

        with col_izq:
            lat, lon, direccion, depto = mostrar_mapa_selector()
            if lat:
                st.success(f"📍 **{direccion}**")
                MAPPING_ZONAS = {'TUMBES':4,'PIURA':4,'LAMBAYEQUE':4,'LA LIBERTAD':4,'ANCASH':4,'LIMA':4,'CALLAO':4,'ICA':4,'AREQUIPA':4,'MOQUEGUA':4,'TACNA':4,'CAJAMARCA':3,'SAN MARTIN':3,'HUANCAVELICA':3,'AYACUCHO':3,'APURIMAC':3,'PASCO':3,'JUNIN':3,'AMAZONAS':2,'HUANUCO':2,'UCAYALI':2,'CUSCO':2,'PUNO':2,'LORETO':1,'MADRE DE DIOS':1}
                if depto:
                    if "last_depto" not in st.session_state or st.session_state["last_depto"] != depto:
                        st.session_state["last_depto"] = depto
                        st.session_state["zona_seleccionada"] = MAPPING_ZONAS.get(depto, 4)
                        st.rerun()

        with col_der:
            st.subheader("⚙️ Parámetros de Diseño")
            
            # --- SECCIÓN 1: ZONA, SUELO, USO ---
            c1, c2, c3 = st.columns(3)
            if "zona_seleccionada" not in st.session_state: st.session_state["zona_seleccionada"] = 4
            zona = c1.selectbox("Zona (Z)", [4, 3, 2, 1], key="zona_seleccionada")
            
            # Listas inteligentes desde la clase
            lista_suelos = list(norma.factor_S.keys())
            suelo = c2.selectbox("Suelo (S)", lista_suelos, index=1)
            
            lista_usos = list(norma.categorias.keys())
            cat = c3.selectbox("Categoría (U)", lista_usos, index=2)

            st.markdown("---")
            st.write("🏗️ **Sistema Estructural y Regularidad (Cálculo de R)**")
            
            # --- SECCIÓN 2: CONFIGURACIÓN ESTRUCTURAL (X e Y) ---
            tabs_dir = st.tabs(["Dirección X-X", "Dirección Y-Y"])
            
            with tabs_dir[0]:
                sis_x = st.selectbox("Sistema Estructural X", list(norma.sistemas_estructurales.keys()), index=5, key="sx")
                c_ia_x, c_ip_x = st.columns(2)
                ia_x = c_ia_x.selectbox("Irregularidad Altura (Ia)", list(norma.irregularidad_altura.keys()), key="iax")
                ip_x = c_ip_x.selectbox("Irregularidad Planta (Ip)", list(norma.irregularidad_planta.keys()), key="ipx")
            
            with tabs_dir[1]:
                sis_y = st.selectbox("Sistema Estructural Y", list(norma.sistemas_estructurales.keys()), index=5, key="sy")
                c_ia_y, c_ip_y = st.columns(2)
                ia_y = c_ia_y.selectbox("Irregularidad Altura (Ia)", list(norma.irregularidad_altura.keys()), key="iay")
                ip_y = c_ip_y.selectbox("Irregularidad Planta (Ip)", list(norma.irregularidad_planta.keys()), key="ipy")

            st.markdown("---")
            st.write("📏 **Unidades**")
            unidad = st.radio("Output:", ["g", "m/s²"], horizontal=True, label_visibility="collapsed")
            factor_g = 9.81 if unidad == "m/s²" else 1.0
            label_eje = "Aceleración (m/s²)" if unidad == "m/s²" else "Aceleración (g)"

            ejecutar = st.button("🚀 Calcular Espectros Combinados", type="primary", use_container_width=True)

            if ejecutar:
                # Empaquetar parámetros
                input_params = {
                    'zona': zona, 'suelo': suelo, 'categoria': cat,
                    'sistema_x': sis_x, 'ia_x': ia_x, 'ip_x': ip_x,
                    'sistema_y': sis_y, 'ia_y': ia_y, 'ip_y': ip_y
                }
                
                # Calcular (El método get_spectrum_curve ahora recibe todo y calcula R dentro)
                Tx, Sa_x_des_raw, Sa_y_des_raw, Sa_el_raw, info = norma.get_spectrum_curve(input_params)

                if info.get('Error'):
                    st.error(info['Error'])
                else:
                    # Conversión
                    Sa_el = Sa_el_raw * factor_g
                    Sa_x_des = Sa_x_des_raw * factor_g
                    Sa_y_des = Sa_y_des_raw * factor_g

                    # Resumen Paramétrico Mejorado
                    st.markdown("### 📝 Resultados de Parámetros")
                    
                    # Fila 1: Factores Básicos
                    p1, p2, p3, p4, p5 = st.columns(5)
                    p1.markdown(f'<div class="custom-metric"><p class="metric-label">Z</p><p class="metric-value">{info["Z"]}g</p></div>', unsafe_allow_html=True)
                    p2.markdown(f'<div class="custom-metric"><p class="metric-label">U</p><p class="metric-value">{info["U"]}</p></div>', unsafe_allow_html=True)
                    p3.markdown(f'<div class="custom-metric"><p class="metric-label">S</p><p class="metric-value">{info["S"]}</p></div>', unsafe_allow_html=True)
                    p4.markdown(f'<div class="custom-metric"><p class="metric-label">TP</p><p class="metric-value">{info["TP"]}s</p></div>', unsafe_allow_html=True)
                    p5.markdown(f'<div class="custom-metric"><p class="metric-label">TL</p><p class="metric-value">{info["TL"]}s</p></div>', unsafe_allow_html=True)
                    
                    # Fila 2: Coeficientes R Calculados
                    r1, r2 = st.columns(2)
                    r1.info(f"**Dirección X:** R = {info['R0_x']} x {norma.irregularidad_altura[ia_x]} x {norma.irregularidad_planta[ip_x]} = **{info['Rx']:.2f}**")
                    r2.info(f"**Dirección Y:** R = {info['R0_y']} x {norma.irregularidad_altura[ia_y]} x {norma.irregularidad_planta[ip_y]} = **{info['Ry']:.2f}**")

                    # Gráfico
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=Tx, y=Sa_el, mode='lines', line=dict(color='red', width=2, dash='dash'), name='Elástico (R=1)'))
                    fig.add_trace(go.Scatter(x=Tx, y=Sa_x_des, mode='lines', fill='tonexty', fillcolor='rgba(255, 0, 0, 0.15)', line=dict(color='black', width=3), name=f'Diseño X (R={info["Rx"]:.2f})'))
                    fig.add_trace(go.Scatter(x=Tx, y=Sa_y_des, mode='lines', line=dict(color='blue', width=2), name=f'Diseño Y (R={info["Ry"]:.2f})'))

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
                            f"Sa Elástico": Sa_el,
                            f"Sa Diseño X": Sa_x_des,
                            f"Sa Diseño Y": Sa_y_des
                        })
                        st.dataframe(df, use_container_width=True, height=200)
                        
                        col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
                        
                        txt_x = df.iloc[:, [0, 2]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                        txt_y = df.iloc[:, [0, 3]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                        
                        col_d1.download_button(f"📥 ETABS Dir X", txt_x, f"Espectro_X.txt", "text/plain")
                        col_d2.download_button(f"📥 ETABS Dir Y", txt_y, f"Espectro_Y.txt", "text/plain")
                        
                        img_bytes = fig.to_image(format="png", width=800, height=400, scale=2)
                        img_stream = io.BytesIO(img_bytes)
                        
                        # Datos para el PDF (incluye los nombres largos de irregularidades)
                        report_params = {
                            'suelo': suelo, 'categoria': cat, 
                            'sistema_x': sis_x, 'rx_final': info['Rx'],
                            'sistema_y': sis_y, 'ry_final': info['Ry'],
                            'unidad': unidad, 'direccion': direccion
                        }
                        
                        pdf_bytes = create_pdf(report_params, info, direccion, df, img_stream)
                        col_d3.download_button("📄 Reporte PDF", pdf_bytes, "Memoria_SOFIPS.pdf", "application/pdf", type="primary")

    else:
        st.warning(f"⚠️ El módulo para **{pais_seleccionado}** está en desarrollo.")

elif modulo == "Verificación E.030 (ETABS)":
    # (Mantener el código del auditor de ETABS que ya teníamos o dejar un placeholder)
    st.info("ℹ️ Sube tu Excel exportado de ETABS (File > Export > Excel). Asegúrate de incluir la tabla **'Story Drifts'**.")
    uploaded_file = st.file_uploader("Archivo de Resultados (.xlsx)", type=["xlsx"])
    if uploaded_file:
        auditor = EtabsValidator(uploaded_file)
        exito, msg = auditor.cargar_datos()
        if exito:
            st.success(msg)
            # Lógica de verificación
        else:
            st.error(msg)