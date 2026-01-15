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
from core.location_data import LocationData

# 1. CONFIGURACIÓN
st.set_page_config(page_title="SOFIPS | Suite Sísmica", layout="wide", page_icon="🏗️", initial_sidebar_state="expanded")

# CSS Global
st.markdown("""
<style>
/* Forzar ancho completo en contenedores */
.block-container { padding-top: 1rem; padding-bottom: 5rem; }
.st-emotion-cache-16cqk79 { width: 100%; }
.custom-metric { background-color: #f8f9fa; border-left: 5px solid #0055A4; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 5px; }
.metric-label { font-size: 11px; color: #666; font-weight: 700; text-transform: uppercase; }
.metric-value { font-size: 20px; font-weight: 800; color: #2C3E50; }
</style>
""", unsafe_allow_html=True)

# FUNCIONES AYUDA
@st.dialog("📘 Tablas Normativas")
def ver_galeria_tablas(lista_imagenes, caption_general):
    st.subheader(caption_general)
    for img_name in lista_imagenes:
        path = f"assets/tablas/{img_name}"
        if os.path.exists(path):
            st.image(path, use_container_width=True)
        else:
            st.warning(f"⚠️ Falta imagen: {img_name}")

def control_con_ayuda_galeria(label_sel, opciones, key, lista_imgs, index=0, on_change=None):
    c1, c2 = st.columns([0.85, 0.15])
    with c1: val = st.selectbox(label_sel, opciones, index=index, key=key, on_change=on_change)
    with c2: 
        st.write(""); st.write("") 
        if st.button("👁️", key=f"btn_{key}", help="Ver tabla"): ver_galeria_tablas(lista_imgs, label_sel)
    return val

# HEADER
c_logo, c_text = st.columns([0.25, 0.75])
with c_logo:
    if os.path.exists("assets/logo.png"):
        with open("assets/logo.png", "rb") as f: img_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<img src="data:image/png;base64,{img_b64}" style="width: 260px; max-width: 100%;">', unsafe_allow_html=True)
with c_text:
    st.markdown("""
        <div style="height: 120px; display: flex; flex-direction: column; justify-content: center;">
            <h3 style="margin:0; color:#2C3E50; font-size:28px; font-weight:bold;">SOFIPS: Software informático de análisis y diseño sismorresistente</h3>
            <p style="margin:5px 0 0 0; color:gray;">Desarrollo: <b>Ing. Arnold Mendo Rodriguez</b> | Norma E.030</p>
        </div>
    """, unsafe_allow_html=True)
st.markdown("---")

# INICIO LÓGICA
loc_data = LocationData()
norma = NormaE030()

# PESTAÑAS PRINCIPALES
tab_ubicacion, tab_espectro, tab_tablas = st.tabs(["📍 1. Ubicación y Zonificación", "📊 2. Espectro de Diseño", "📋 3. Tablas y Reportes"])

# === PESTAÑA 1: UBICACIÓN ===
with tab_ubicacion:
    col_sel, col_map = st.columns([1, 2])
    
    # Selectores de Base de Datos
    with col_sel:
        st.subheader("🔍 Selección de Lugar")
        
        deptos = loc_data.get_departamentos()
        depto_sel = st.selectbox("Departamento", deptos, key="sel_depto")
        
        provs = loc_data.get_provincias(depto_sel) if depto_sel else []
        prov_sel = st.selectbox("Provincia", provs, key="sel_prov")
        
        dist_sel = None
        coord_update = None
        zoom_update = None
        
        if prov_sel:
            df_distritos = loc_data.get_distritos_data(prov_sel)
            dist_nombres = df_distritos['Distrito'].tolist()
            dist_sel = st.selectbox("Distrito", dist_nombres, key="sel_dist")
            
            if dist_sel:
                # Obtener datos del distrito seleccionado
                row_dist = df_distritos[df_distritos['Distrito'] == dist_sel].iloc[0]
                lat_d, lon_d = row_dist['Latitud'], row_dist['Longitud']
                zona_d = int(row_dist['Zona sismica'])
                
                # Actualizar Zona Sísmica en Sesión
                if "zona_seleccionada" not in st.session_state or st.session_state.zona_seleccionada != zona_d:
                    st.session_state.zona_seleccionada = zona_d
                    st.toast(f"✅ Zona {zona_d} asignada (Distrito: {dist_sel})", icon="🌍")
                
                # Preparar coordenadas para mover el mapa
                coord_update = [lat_d, lon_d]
                zoom_update = 13
                st.info(f"**Datos E.030:**\n- Zona: **{zona_d}**\n- Lat: {lat_d}\n- Lon: {lon_d}")

    # Mapa (Ocupa columna derecha)
    with col_map:
        # LLAMADA CORREGIDA: Recibe 4 valores y acepta force_center
        lat_pin, lon_pin, dir_pin, depto_pin = mostrar_mapa_selector(force_center=coord_update, force_zoom=zoom_update)
        
        # Si el usuario hace clic en el mapa (no usa selectores), actualizamos zona aproximada
        if depto_pin and not coord_update:
            MAPPING_ZONAS = {'TUMBES':4,'PIURA':4,'LAMBAYEQUE':4,'LA LIBERTAD':4,'ANCASH':4,'LIMA':4,'CALLAO':4,'ICA':4,'AREQUIPA':4,'MOQUEGUA':4,'TACNA':4,'CAJAMARCA':3,'SAN MARTIN':3,'HUANCAVELICA':3,'AYACUCHO':3,'APURIMAC':3,'PASCO':3,'JUNIN':3,'AMAZONAS':2,'HUANUCO':2,'UCAYALI':2,'CUSCO':2,'PUNO':2,'LORETO':1,'MADRE DE DIOS':1}
            # Limpieza básica
            d_clean = depto_pin.replace("DEPARTAMENTO DE ", "").strip()
            z_map = MAPPING_ZONAS.get(d_clean, 4)
            if "zona_seleccionada" not in st.session_state or st.session_state.zona_seleccionada != z_map:
                st.session_state.zona_seleccionada = z_map
                st.rerun()

# === PESTAÑA 2: ESPECTRO ===
with tab_espectro:
    # Variables de estado
    if "u_val" not in st.session_state: st.session_state["u_val"] = 1.0
    if "r0_x" not in st.session_state: st.session_state["r0_x"] = 8.0
    if "ia_x" not in st.session_state: st.session_state["ia_x"] = 1.0
    if "ip_x" not in st.session_state: st.session_state["ip_x"] = 1.0
    if "r0_y" not in st.session_state: st.session_state["r0_y"] = 8.0
    if "ia_y" not in st.session_state: st.session_state["ia_y"] = 1.0
    if "ip_y" not in st.session_state: st.session_state["ip_y"] = 1.0
    if "zona_seleccionada" not in st.session_state: st.session_state["zona_seleccionada"] = 4

    col_param, col_graf = st.columns([1, 1.5], gap="medium")

    with col_param:
        st.subheader("⚙️ Parámetros")
        
        # Zona (Automática)
        idx_zona = [4, 3, 2, 1].index(st.session_state.zona_seleccionada)
        zona = st.selectbox("Zona (Z)", [4, 3, 2, 1], index=idx_zona, key="zona_key")
        
        # Suelo
        suelo = control_con_ayuda_galeria("Suelo (S)", list(norma.factor_S.keys()), "suelo_key", ["tabla_2.png", "tabla_3.png", "tabla_4.png", "tabla_5.png"], index=1)
        
        # Categoría
        def update_u(): st.session_state.u_val = norma.categorias[st.session_state.cat_key]
        cat_sel = control_con_ayuda_galeria("Categoría (U)", list(norma.categorias.keys()), "cat_key", ["tabla_7.png"], index=2, on_change=update_u)
        u_final = st.number_input("Valor U", value=st.session_state.u_val, format="%.2f", step=0.1)

        st.markdown("---")
        st.write("🏗️ **Sistema (R)**")
        
        tab_sx, tab_sy = st.tabs(["X", "Y"])
        imgs_sis = ["tabla_10.png"]
        imgs_ia = ["tabla_irregularidad_altura.png"]
        imgs_ip = ["tabla_irregularidad_planta.png"]

        # Dir X
        with tab_sx:
            def rx_upd(): 
                st.session_state.r0_x = norma.sistemas_estructurales[st.session_state.sis_x]
                st.session_state.ia_x = norma.irregularidad_altura[st.session_state.iax]
                st.session_state.ip_x = norma.irregularidad_planta[st.session_state.ipx]
            
            control_con_ayuda_galeria("Sistema X", list(norma.sistemas_estructurales.keys()), "sis_x", imgs_sis, index=5, on_change=rx_upd)
            control_con_ayuda_galeria("Irreg. Alt", list(norma.irregularidad_altura.keys()), "iax", imgs_ia, index=0, on_change=rx_upd)
            control_con_ayuda_galeria("Irreg. Pla", list(norma.irregularidad_planta.keys()), "ipx", imgs_ip, index=0, on_change=rx_upd)
            rx_final = st.session_state.r0_x * st.session_state.ia_x * st.session_state.ip_x
            st.info(f"R Final X = {rx_final:.2f}")

        # Dir Y
        with tab_sy:
            def ry_upd(): 
                st.session_state.r0_y = norma.sistemas_estructurales[st.session_state.sis_y]
                st.session_state.ia_y = norma.irregularidad_altura[st.session_state.iay]
                st.session_state.ip_y = norma.irregularidad_planta[st.session_state.ipy]
            
            control_con_ayuda_galeria("Sistema Y", list(norma.sistemas_estructurales.keys()), "sis_y", imgs_sis, index=5, on_change=ry_upd)
            control_con_ayuda_galeria("Irreg. Alt", list(norma.irregularidad_altura.keys()), "iay", imgs_ia, index=0, on_change=ry_upd)
            control_con_ayuda_galeria("Irreg. Pla", list(norma.irregularidad_planta.keys()), "ipy", imgs_ip, index=0, on_change=ry_upd)
            ry_final = st.session_state.r0_y * st.session_state.ia_y * st.session_state.ip_y
            st.info(f"R Final Y = {ry_final:.2f}")

    with col_graf:
        st.subheader("📈 Resultados")
        unidad = st.radio("Unidades", ["g", "m/s²"], horizontal=True)
        factor = 9.81 if unidad == "m/s²" else 1.0
        
        # Calcular
        input_params = {'zona': zona, 'suelo': suelo, 'categoria': cat_sel, 'u_val': u_final, 'rx_val': rx_final, 'ry_val': ry_final}
        Tx, Sa_x_raw, Sa_y_raw, Sa_el_raw, info = norma.get_spectrum_curve(input_params)
        
        # Convertir
        Sa_el = Sa_el_raw * factor
        Sa_x = Sa_x_raw * factor
        Sa_y = Sa_y_raw * factor
        
        # Gráfica
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Tx, y=Sa_el, name="Elástico (R=1)", line=dict(color='red', width=2, dash='dash')))
        fig.add_trace(go.Scatter(x=Tx, y=Sa_x, name=f"Diseño X (R={rx_final:.2f})", fill='tonexty', fillcolor='rgba(255,0,0,0.1)', line=dict(color='black', width=3)))
        fig.add_trace(go.Scatter(x=Tx, y=Sa_y, name=f"Diseño Y (R={ry_final:.2f})", line=dict(color='blue', width=2)))
        fig.update_layout(template="plotly_white", height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        # Resumen
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Z", f"{info['Z']}g"); c2.metric("U", info['U']); c3.metric("S", info['S']); c4.metric("TP", f"{info['TP']}s"); c5.metric("TL", f"{info['TL']}s")

# === PESTAÑA 3: REPORTES ===
with tab_tablas:
    st.subheader("📋 Tablas y Descargas")
    df = pd.DataFrame({"Periodo": Tx, f"Sa Elástico ({unidad})": Sa_el, f"Sa X": Sa_x, f"Sa Y": Sa_y})
    st.dataframe(df, use_container_width=True)
    
    # Botones descarga
    txt_x = df.iloc[:, [0, 2]].to_csv(sep='\t', index=False, header=False).encode('utf-8')
    st.download_button("📥 ETABS X", txt_x, f"Espectro_X.txt")