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
from core.norma_e030 import NormaE030

# 1. Configuración
st.set_page_config(page_title="SOFIPS | Suite Sísmica", layout="wide", page_icon="🏗️", initial_sidebar_state="expanded")

# CSS Global
st.markdown("""
<style>
.st-emotion-cache-16cqk79, .leaflet-container, .leaflet-grab, .leaflet-interactive { cursor: crosshair !important; }
.custom-metric { background-color: #f8f9fa; border-left: 5px solid #0055A4; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.metric-label { font-size: 11px; color: #666; margin: 0; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
.metric-value { font-size: 22px; font-weight: 800; color: #2C3E50; margin: 5px 0 0 0; }
/* Ajuste para alinear verticalmente el botón de ojo en el sidebar */
div[data-testid="stHorizontalBlock"] { align-items: end; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE AYUDA (MODALES) ---
@st.dialog("📘 Referencia Normativa")
def ver_imagen_grande(path, caption):
    if os.path.exists(path):
        st.image(path, caption=caption, use_container_width=True)
    else:
        st.error(f"⚠️ Falta la imagen: {path}")

def control_con_ayuda(label_sel, opciones, key, path_img, index=0, on_change=None):
    """Crea un selector y un botón de ayuda alineados en el sidebar"""
    c1, c2 = st.columns([0.85, 0.15])
    with c1:
        val = st.selectbox(label_sel, opciones, index=index, key=key, on_change=on_change)
    with c2:
        # El CSS arriba alinea esto al fondo, así que no necesitamos espaciadores
        if st.button("👁️", key=f"btn_{key}", help=f"Ver tabla normativa"):
            ver_imagen_grande(path_img, label_sel)
    return val

# ---------------------------------------------------------
# BARRA LATERAL (CONTROLES)
# ---------------------------------------------------------
with st.sidebar:
    # Logo
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    st.markdown("---")
    
    # Selector de País y Módulo
    manager = SeismicManager()
    pais = st.selectbox("📍 Normativa", list(manager.available_codes.keys()))
    modulo = st.radio("🛠️ Herramienta", ["Espectro de Diseño", "Verificación E.030"])
    
    st.markdown("---")

    # CONTROLES DE DISEÑO
    if modulo == "Espectro de Diseño" and "Perú" in pais:
        norma = NormaE030()
        st.subheader("⚙️ Parámetros E.030")
        
        # Inicializar estado
        if "zona_seleccionada" not in st.session_state: st.session_state["zona_seleccionada"] = 4
        if "u_val" not in st.session_state: st.session_state["u_val"] = 1.0

        # 1. ZONA, SUELO, USO (Con Ayuda)
        zona = control_con_ayuda("Zona (Z)", [4, 3, 2, 1], "zona_key", "assets/mapa_zonas.png", index=0)
        if zona != st.session_state.zona_seleccionada: st.session_state.zona_seleccionada = zona
        
        suelo = control_con_ayuda("Perfil de Suelo (S)", list(norma.factor_S.keys()), "suelo_key", "assets/tabla_suelos.png", index=1)
        
        def update_u(): st.session_state.u_val = norma.categorias[st.session_state.cat_key]
        cat_sel = control_con_ayuda("Categoría (U)", list(norma.categorias.keys()), "cat_key", "assets/tabla_categorias.png", index=2, on_change=update_u)
        
        u_final = st.number_input("Valor U (Editable)", value=st.session_state.u_val, format="%.2f", step=0.1)

        st.markdown("---")
        st.subheader("🏗️ Sistema Estructural (R)")
        
        tab_x, tab_y = st.tabs(["Dir X", "Dir Y"])
        
        # INICIALIZAR R
        if "r0_x" not in st.session_state: 
            for k in ["r0_x","ia_x","ip_x","r0_y","ia_y","ip_y"]: st.session_state[k] = 1.0
            st.session_state["r0_x"] = 8.0; st.session_state["r0_y"] = 8.0

        # DIR X (Con Ayuda)
        with tab_x:
            def upd_rx(): 
                st.session_state.r0_x = norma.sistemas_estructurales[st.session_state.sis_x_key]
                st.session_state.ia_x = norma.irregularidad_altura[st.session_state.ia_x_key]
                st.session_state.ip_x = norma.irregularidad_planta[st.session_state.ip_x_key]

            # Aquí implementamos control_con_ayuda para los sistemas e irregularidades
            control_con_ayuda("Sistema X", list(norma.sistemas_estructurales.keys()), "sis_x_key", "assets/tabla_sistemas.png", index=5, on_change=upd_rx)
            control_con_ayuda("Irreg. Altura", list(norma.irregularidad_altura.keys()), "ia_x_key", "assets/tabla_irregularidad_altura.png", index=0, on_change=upd_rx)
            control_con_ayuda("Irreg. Planta", list(norma.irregularidad_planta.keys()), "ip_x_key", "assets/tabla_irregularidad_planta.png", index=0, on_change=upd_rx)
            
            c_rx_in, c_rx_out = st.columns([1, 1])
            r0_x_val = c_rx_in.number_input("R0 X", value=st.session_state.r0_x)
            ia_x_val = st.session_state.ia_x
            ip_x_val = st.session_state.ip_x
            rx_final = r0_x_val * ia_x_val * ip_x_val
            c_rx_out.metric("R Final", f"{rx_final:.2f}")

        # DIR Y (Con Ayuda)
        with tab_y:
            def upd_ry(): 
                st.session_state.r0_y = norma.sistemas_estructurales[st.session_state.sis_y_key]
                st.session_state.ia_y = norma.irregularidad_altura[st.session_state.ia_y_key]
                st.session_state.ip_y = norma.irregularidad_planta[st.session_state.ip_y_key]

            control_con_ayuda("Sistema Y", list(norma.sistemas_estructurales.keys()), "sis_y_key", "assets/tabla_sistemas.png", index=5, on_change=upd_ry)
            control_con_ayuda("Irreg. Altura Y", list(norma.irregularidad_altura.keys()), "ia_y_key", "assets/tabla_irregularidad_altura.png", index=0, on_change=upd_ry)
            control_con_ayuda("Irreg. Planta Y", list(norma.irregularidad_planta.keys()), "ip_y_key", "assets/tabla_irregularidad_planta.png", index=0, on_change=upd_ry)
            
            c_ry_in, c_ry_out = st.columns([1, 1])
            r0_y_val = c_ry_in.number_input("R0 Y", value=st.session_state.r0_y)
            ia_y_val = st.session_state.ia_y
            ip_y_val = st.session_state.ip_y
            ry_final = r0_y_val * ia_y_val * ip_y_val
            c_ry_out.metric("R Final", f"{ry_final:.2f}")
        
        st.markdown("---")
        unidad = st.radio("Unidades:", ["g", "m/s²"], horizontal=True)
        factor_g = 9.81 if unidad == "m/s²" else 1.0
        label_eje = "Aceleración (m/s²)" if unidad == "m/s²" else "Aceleración (g)"
        
        ejecutar = st.button("🚀 Calcular", type="primary", use_container_width=True)

# ---------------------------------------------------------
# ÁREA PRINCIPAL
# ---------------------------------------------------------
logo_header = "assets/logo.png"
if os.path.exists(logo_header):
    with open(logo_header, "rb") as f: img_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <div style="display:flex; align-items:center; margin-bottom:20px;">
        <img src="data:image/png;base64,{img_b64}" style="height:60px; margin-right:15px;">
        <div>
            <h2 style="margin:0; color:#2C3E50;">SOFIPS: Ingeniería Sísmica Avanzada</h2>
            <p style="margin:0; color:gray;">Desarrollo: Ing. Arnold Mendo Rodriguez</p>
        </div>
    </div>
    <hr style="margin-top:0;">
    """, unsafe_allow_html=True)

if modulo == "Espectro de Diseño":
    
    lat, lon, direccion, depto = mostrar_mapa_selector()
    if lat:
        st.success(f"📍 **Ubicación:** {direccion}")
        MAPPING_ZONAS = {'TUMBES':4,'PIURA':4,'LAMBAYEQUE':4,'LA LIBERTAD':4,'ANCASH':4,'LIMA':4,'CALLAO':4,'ICA':4,'AREQUIPA':4,'MOQUEGUA':4,'TACNA':4,'CAJAMARCA':3,'SAN MARTIN':3,'HUANCAVELICA':3,'AYACUCHO':3,'APURIMAC':3,'PASCO':3,'JUNIN':3,'AMAZONAS':2,'HUANUCO':2,'UCAYALI':2,'CUSCO':2,'PUNO':2,'LORETO':1,'MADRE DE DIOS':1}
        if depto:
            if "last_depto" not in st.session_state or st.session_state["last_depto"] != depto:
                st.session_state["last_depto"] = depto
                st.session_state["zona_seleccionada"] = MAPPING_ZONAS.get(depto, 4)
                st.rerun()

    if ejecutar:
        norma = NormaE030()
        
        if st.session_state.zona_seleccionada != zona:
             zona_calc = zona
        else:
             zona_calc = st.session_state.zona_seleccionada

        input_params = {
            'zona': zona_calc, 'suelo': suelo, 'categoria': cat_sel,
            'u_val': u_final, 'rx_val': rx_final, 'ry_val': ry_final
        }

        Tx, Sa_x_des_raw, Sa_y_des_raw, Sa_el_raw, info = norma.get_spectrum_curve(input_params)

        if info.get('Error'):
            st.error(info['Error'])
        else:
            Sa_el = Sa_el_raw * factor_g
            Sa_x_des = Sa_x_des_raw * factor_g
            Sa_y_des = Sa_y_des_raw * factor_g

            st.markdown("### 📊 Resultados del Análisis")
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.markdown(f'<div class="custom-metric"><p class="metric-label">ZONA (Z)</p><p class="metric-value">{info["Z"]}g</p></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="custom-metric"><p class="metric-label">USO (U)</p><p class="metric-value">{info["U"]}</p></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="custom-metric"><p class="metric-label">SUELO (S)</p><p class="metric-value">{info["S"]}</p></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="custom-metric"><p class="metric-label">TP</p><p class="metric-value">{info["TP"]}s</p></div>', unsafe_allow_html=True)
            c5.markdown(f'<div class="custom-metric"><p class="metric-label">TL</p><p class="metric-value">{info["TL"]}s</p></div>', unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=Tx, y=Sa_el, mode='lines', line=dict(color='red', width=2, dash='dash'), name='Elástico (R=1)'))
            fig.add_trace(go.Scatter(x=Tx, y=Sa_x_des, mode='lines', fill='tonexty', fillcolor='rgba(255, 0, 0, 0.1)', line=dict(color='black', width=3), name=f'Diseño X (R={rx_final:.2f})'))
            fig.add_trace(go.Scatter(x=Tx, y=Sa_y_des, mode='lines', line=dict(color='blue', width=2), name=f'Diseño Y (R={ry_final:.2f})'))

            fig.update_layout(
                title=dict(text=f"<b>ESPECTRO DE DISEÑO SÍSMICO ({label_eje})</b>", font=dict(size=18)),
                xaxis=dict(title="Periodo T (s)", showgrid=True, gridcolor='#eee'),
                yaxis=dict(title=label_eje, showgrid=True, gridcolor='#eee'),
                template="plotly_white", 
                height=600,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            col_tab, col_down = st.columns([2, 1])
            
            with col_tab:
                st.write("📋 **Tabla de Valores**")
                df = pd.DataFrame({"T(s)": Tx, f"Sa_Elas": Sa_el, f"Sa_X": Sa_x_des, f"Sa_Y": Sa_y_des})
                st.dataframe(df, use_container_width=True, height=250)

            with col_down:
                st.write("💾 **Exportar Datos**")
                txt_x = df.iloc[:, [0, 2]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                txt_y = df.iloc[:, [0, 3]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
                
                st.download_button(f"📥 TXT para ETABS (Dir X)", txt_x, f"Espectro_X.txt", "text/plain", use_container_width=True)
                st.download_button(f"📥 TXT para ETABS (Dir Y)", txt_y, f"Espectro_Y.txt", "text/plain", use_container_width=True)
                
                img_bytes = fig.to_image(format="png", width=1000, height=500, scale=2)
                img_stream = io.BytesIO(img_bytes)
                
                report_params = {
                    'suelo': suelo, 'categoria': cat_sel, 
                    'rx': rx_final, 'ry': ry_final, 
                    'unidad': unidad, 'direccion': direccion,
                    'sistema_x': st.session_state.sis_x_key,
                    'sistema_y': st.session_state.sis_y_key,
                    'r0_x': r0_x_val, 'ia_x': ia_x_val, 'ip_x': ip_x_val,
                    'r0_y': r0_y_val, 'ia_y': ia_y_val, 'ip_y': ip_y_val
                }
                pdf_bytes = create_pdf(report_params, info, direccion, df, img_stream)
                st.download_button("📄 Reporte Profesional PDF", pdf_bytes, "Memoria_SOFIPS.pdf", "application/pdf", type="primary", use_container_width=True)

elif modulo == "Verificación E.030":
    st.info("Módulo en construcción...")