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

# --- HEADER ---
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

# --- INICIALIZACIÓN DE ESTADO (Session State) ---
# Esto permite que los inputs numéricos reaccionen a los dropdowns
if "u_val" not in st.session_state: st.session_state["u_val"] = 1.0
if "r0_x" not in st.session_state: st.session_state["r0_x"] = 8.0
if "ia_x" not in st.session_state: st.session_state["ia_x"] = 1.0
if "ip_x" not in st.session_state: st.session_state["ip_x"] = 1.0
if "r0_y" not in st.session_state: st.session_state["r0_y"] = 8.0
if "ia_y" not in st.session_state: st.session_state["ia_y"] = 1.0
if "ip_y" not in st.session_state: st.session_state["ip_y"] = 1.0

# --- LAYOUT ---
col_izq, col_der = st.columns([1, 1.4], gap="large")

# COLUMNA IZQUIERDA: MAPA
with col_izq:
    lat, lon, direccion, depto = mostrar_mapa_selector()
    if lat:
        st.success(f"📍 **Ubicación:** {direccion}")
        MAPPING_ZONAS = {'TUMBES':4,'PIURA':4,'LAMBAYEQUE':4,'LA LIBERTAD':4,'ANCASH':4,'LIMA':4,'CALLAO':4,'ICA':4,'AREQUIPA':4,'MOQUEGUA':4,'TACNA':4,'CAJAMARCA':3,'SAN MARTIN':3,'HUANCAVELICA':3,'AYACUCHO':3,'APURIMAC':3,'PASCO':3,'JUNIN':3,'AMAZONAS':2,'HUANUCO':2,'UCAYALI':2,'CUSCO':2,'PUNO':2,'LORETO':1,'MADRE DE DIOS':1}
        if depto:
            if "last_depto" not in st.session_state or st.session_state["last_depto"] != depto:
                st.session_state["last_depto"] = depto
                st.session_state["zona_seleccionada"] = MAPPING_ZONAS.get(depto, 4)
                st.rerun()

# COLUMNA DERECHA: PARAMETROS
with col_der:
    st.subheader("⚙️ Parámetros de Diseño")
    
    # Instancia de norma
    norma = NormaE030()

    # --- ZONA Y SUELO ---
    c1, c2 = st.columns(2)
    if "zona_seleccionada" not in st.session_state: st.session_state["zona_seleccionada"] = 4
    zona = c1.selectbox("Zona (Z)", [4, 3, 2, 1], key="zona_seleccionada")
    suelo = c2.selectbox("Suelo (S)", list(norma.factor_S.keys()), index=1)
    
    # --- CATEGORIA (U) con Actualización Automática ---
    def update_u():
        st.session_state.u_val = norma.categorias[st.session_state.cat_key]

    c3, c4 = st.columns([2, 1])
    # Selectbox actualiza el número
    cat_sel = c3.selectbox("Categoría (U)", list(norma.categorias.keys()), index=4, key="cat_key", on_change=update_u)
    # Number input es editable
    u_final = c4.number_input("Valor U", value=st.session_state.u_val, format="%.2f", step=0.1)

    st.markdown("---")
    st.write("🏗️ **Coeficientes de Reducción (R)**")

    # --- TABS PARA X e Y ---
    tabs = st.tabs(["Dirección X-X", "Dirección Y-Y"])

    # === DIRECCIÓN X ===
    with tabs[0]:
        def update_rx_components():
            st.session_state.r0_x = norma.sistemas_estructurales[st.session_state.sis_x_key]
            st.session_state.ia_x = norma.irregularidad_altura[st.session_state.ia_x_key]
            st.session_state.ip_x = norma.irregularidad_planta[st.session_state.ip_x_key]
        
        # Selectores
        st.selectbox("Sistema Estructural X", list(norma.sistemas_estructurales.keys()), index=6, key="sis_x_key", on_change=update_rx_components)
        c_rx1, c_rx2 = st.columns(2)
        c_rx1.selectbox("Irregularidad Altura (Ia)", list(norma.irregularidad_altura.keys()), key="ia_x_key", on_change=update_rx_components)
        c_rx2.selectbox("Irregularidad Planta (Ip)", list(norma.irregularidad_planta.keys()), key="ip_x_key", on_change=update_rx_components)
        
        # Inputs Numéricos Editables
        st.markdown("**Valores Numéricos (Editables):**")
        cx1, cx2, cx3, cx4 = st.columns([1, 1, 1, 1.5])
        r0_x_val = cx1.number_input("R0 X", value=st.session_state.r0_x, step=1.0)
        ia_x_val = cx2.number_input("Ia X", value=st.session_state.ia_x, step=0.05)
        ip_x_val = cx3.number_input("Ip X", value=st.session_state.ip_x, step=0.05)
        
        # R Final Calculado
        rx_final = r0_x_val * ia_x_val * ip_x_val
        cx4.metric("R Final (X)", f"{rx_final:.2f}")

        # Estado de Regularidad
        if ia_x_val < 1.0 or ip_x_val < 1.0:
            st.warning("⚠️ Estructura IRREGULAR en X")
        else:
            st.success("✅ Estructura REGULAR en X")

    # === DIRECCIÓN Y ===
    with tabs[1]:
        def update_ry_components():
            st.session_state.r0_y = norma.sistemas_estructurales[st.session_state.sis_y_key]
            st.session_state.ia_y = norma.irregularidad_altura[st.session_state.ia_y_key]
            st.session_state.ip_y = norma.irregularidad_planta[st.session_state.ip_y_key]
        
        st.selectbox("Sistema Estructural Y", list(norma.sistemas_estructurales.keys()), index=6, key="sis_y_key", on_change=update_ry_components)
        c_ry1, c_ry2 = st.columns(2)
        c_ry1.selectbox("Irregularidad Altura (Ia)", list(norma.irregularidad_altura.keys()), key="ia_y_key", on_change=update_ry_components)
        c_ry2.selectbox("Irregularidad Planta (Ip)", list(norma.irregularidad_planta.keys()), key="ip_y_key", on_change=update_ry_components)
        
        st.markdown("**Valores Numéricos (Editables):**")
        cy1, cy2, cy3, cy4 = st.columns([1, 1, 1, 1.5])
        r0_y_val = cy1.number_input("R0 Y", value=st.session_state.r0_y, step=1.0)
        ia_y_val = cy2.number_input("Ia Y", value=st.session_state.ia_y, step=0.05)
        ip_y_val = cy3.number_input("Ip Y", value=st.session_state.ip_y, step=0.05)
        
        ry_final = r0_y_val * ia_y_val * ip_y_val
        cy4.metric("R Final (Y)", f"{ry_final:.2f}")

        if ia_y_val < 1.0 or ip_y_val < 1.0:
            st.warning("⚠️ Estructura IRREGULAR en Y")
        else:
            st.success("✅ Estructura REGULAR en Y")

    st.markdown("---")
    
    # UNIDADES Y CÁLCULO
    col_u, col_btn = st.columns([1, 2])
    with col_u:
        st.write("📏 **Unidades**")
        unidad = st.radio("Output:", ["g", "m/s²"], horizontal=True, label_visibility="collapsed")
        factor_g = 9.81 if unidad == "m/s²" else 1.0
        label_eje = "Aceleración (m/s²)" if unidad == "m/s²" else "Aceleración (g)"
    
    with col_btn:
        st.write("") # Espacio
        ejecutar = st.button("🚀 Calcular Espectros Combinados", type="primary", use_container_width=True)

    if ejecutar:
        # Paquete de parámetros (Ahora enviamos los valores numéricos finales editados por el usuario)
        input_params = {
            'zona': zona, 'suelo': suelo, 'categoria': cat_sel,
            'u_val': u_final,
            'rx_val': rx_final, 'ry_val': ry_final
        }

        Tx, Sa_x_des_raw, Sa_y_des_raw, Sa_el_raw, info = norma.get_spectrum_curve(input_params)

        if info.get('Error'):
            st.error(info['Error'])
        else:
            Sa_el = Sa_el_raw * factor_g
            Sa_x_des = Sa_x_des_raw * factor_g
            Sa_y_des = Sa_y_des_raw * factor_g

            st.markdown("### 📝 Resumen de Parámetros")
            p1, p2, p3, p4, p5 = st.columns(5)
            p1.markdown(f'<div class="custom-metric"><p class="metric-label">Z</p><p class="metric-value">{info["Z"]}g</p></div>', unsafe_allow_html=True)
            p2.markdown(f'<div class="custom-metric"><p class="metric-label">U</p><p class="metric-value">{info["U"]}</p></div>', unsafe_allow_html=True)
            p3.markdown(f'<div class="custom-metric"><p class="metric-label">S</p><p class="metric-value">{info["S"]}</p></div>', unsafe_allow_html=True)
            p4.markdown(f'<div class="custom-metric"><p class="metric-label">TP</p><p class="metric-value">{info["TP"]}s</p></div>', unsafe_allow_html=True)
            p5.markdown(f'<div class="custom-metric"><p class="metric-label">TL</p><p class="metric-value">{info["TL"]}s</p></div>', unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=Tx, y=Sa_el, mode='lines', line=dict(color='red', width=2, dash='dash'), name='Elástico (R=1)'))
            fig.add_trace(go.Scatter(x=Tx, y=Sa_x_des, mode='lines', fill='tonexty', fillcolor='rgba(255, 0, 0, 0.15)', line=dict(color='black', width=3), name=f'Diseño X (R={rx_final:.2f})'))
            fig.add_trace(go.Scatter(x=Tx, y=Sa_y_des, mode='lines', line=dict(color='blue', width=2), name=f'Diseño Y (R={ry_final:.2f})'))

            fig.update_layout(
                title=dict(text=f"<b>ESPECTRO {label_eje}</b>", font=dict(size=14)),
                xaxis=dict(title="Periodo T (s)", showgrid=True, gridcolor='lightgray'),
                yaxis=dict(title=label_eje, showgrid=True, gridcolor='lightgray'),
                template="plotly_white", height=450, hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Exportación
            with st.expander("📋 Descargas (PDF / Excel / ETABS)", expanded=True):
                df = pd.DataFrame({
                    "T (s)": Tx,
                    f"Sa Elástico ({unidad})": Sa_el,
                    f"Sa Diseño X ({unidad})": Sa_x_des,
                    f"Sa Diseño Y ({unidad})": Sa_y_des
                })
                st.dataframe(df, use_container_width=True, height=200)
                
                c_d1, c_d2, c_d3 = st.columns([1, 1, 1.5])
                txt_x = df.iloc[:, [0, 2]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                txt_y = df.iloc[:, [0, 3]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                c_d1.download_button(f"📥 ETABS Dir X", txt_x, f"Espectro_X.txt", "text/plain")
                c_d2.download_button(f"📥 ETABS Dir Y", txt_y, f"Espectro_Y.txt", "text/plain")
                
                img_bytes = fig.to_image(format="png", width=800, height=400, scale=2)
                img_stream = io.BytesIO(img_bytes)
                report_params = {
                    'suelo': suelo, 'categoria': cat_sel, 
                    'rx': rx_final, 'ry': ry_final, 
                    'unidad': unidad, 'direccion': direccion,
                    'sistema_x': f"{st.session_state.sis_x_key} (Ia={ia_x_val}, Ip={ip_x_val})",
                    'sistema_y': f"{st.session_state.sis_y_key} (Ia={ia_y_val}, Ip={ip_y_val})"
                }
                pdf_bytes = create_pdf(report_params, info, direccion, df, img_stream)
                c_d3.download_button("📄 Reporte PDF", pdf_bytes, "Memoria_SOFIPS.pdf", "application/pdf", type="primary")