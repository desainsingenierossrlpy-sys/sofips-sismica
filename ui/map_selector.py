import streamlit as st
import folium
from streamlit_folium import st_folium

def mostrar_mapa_selector(force_center=None):
    # Vista constante del Perú
    PERU_CENTER = [-9.19, -75.01]
    PERU_ZOOM = 5
    
    if "pin_lat" not in st.session_state:
        st.session_state["pin_lat"] = -12.0464
        st.session_state["pin_lon"] = -77.0428

    if force_center:
        st.session_state["pin_lat"] = force_center[0]
        st.session_state["pin_lon"] = force_center[1]

    m = folium.Map(location=PERU_CENTER, zoom_start=PERU_ZOOM, control_scale=True)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google', name='Google Satélite', overlay=False, control=True
    ).add_to(m)

    folium.Marker(
        [st.session_state["pin_lat"], st.session_state["pin_lon"]], 
        icon=folium.Icon(color="red", icon="crosshairs", prefix='fa'),
        tooltip="Ubicación del Proyecto"
    ).add_to(m)

    # AUMENTO DE ALTURA A 750px para ocupar el espacio vertical
    st_folium(m, width="100%", height=750, key="mapa_v_grande")

    return st.session_state["pin_lat"], st.session_state["pin_lon"]