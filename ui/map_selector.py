import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import unidecode

def mostrar_mapa_selector(force_center=None, force_zoom=None):
    st.markdown("### 📍 Ubicación del Proyecto")
    
    # CSS: Solo para el cursor en cruz, quitamos el forzado de tamaño
    st.markdown("""
    <style>
    .leaflet-container { cursor: crosshair !important; }
    .leaflet-interactive { cursor: crosshair !important; }
    </style>
    """, unsafe_allow_html=True)

    # 1. GESTIÓN DE COORDENADAS Y MEMORIA
    if force_center:
        st.session_state["map_center"] = force_center
        st.session_state["pin_lat"] = force_center[0]
        st.session_state["pin_lon"] = force_center[1]
        if force_zoom: st.session_state["map_zoom"] = force_zoom
        st.rerun()

    # Inicialización por defecto
    if "map_center" not in st.session_state:
        st.session_state["map_center"] = [-9.19, -75.01] # Perú
        st.session_state["map_zoom"] = 5
        st.session_state["pin_lat"] = -12.0464 # Lima
        st.session_state["pin_lon"] = -77.0428

    # 2. CREAR MAPA (BASE ROBUSTA)
    # IMPORTANTE: Usamos 'OpenStreetMap' por defecto para evitar pantalla blanca
    m = folium.Map(
        location=st.session_state["map_center"], 
        zoom_start=st.session_state["map_zoom"],
        control_scale=True,
        tiles="OpenStreetMap" 
    )

    # 3. CAPAS DE GOOGLE (Overlay)
    # Se añaden encima de OSM. Si fallan, al menos se ve el mapa base.
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Híbrido',
        overlay=False, # Si se selecciona, reemplaza base
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Terreno',
        overlay=False,
        control=True
    ).add_to(m)
    
    # 4. CAPA ZONAS E.030
    try:
        folium.GeoJson(
            "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_departamental_simple.geojson",
            name="Zonas E.030",
            style_function=lambda x: {'fillColor': '#FF0000' if x['properties']['NOMBDEP'] == 'LIMA' else '#FFD700', 'color': 'white', 'weight': 0.5, 'fillOpacity': 0.15},
            overlay=True, show=True
        ).add_to(m)
    except:
        pass # Si falla internet, el mapa sigue funcionando

    folium.LayerControl().add_to(m)

    # 5. MARCADOR ROJO
    folium.Marker(
        [st.session_state["pin_lat"], st.session_state["pin_lon"]],
        icon=folium.Icon(color="red", icon="crosshairs", prefix='fa'),
        tooltip="Ubicación Seleccionada"
    ).add_to(m)
    
    # Cartel Flotante
    m.get_root().html.add_child(folium.Element("""
        <div style="position: fixed; top: 10px; left: 50px; width: 220px; background-color: white; border: 2px solid #d33; padding: 5px; z-index:9999; font-size:14px; text-align: center; border-radius: 5px; opacity: 0.9;">
            🎯 <b>Haz CLIC para ubicar</b>
        </div>
    """))

    # 6. RENDERIZAR
    # width=None asegura que se expanda al ancho de la columna
    output = st_folium(m, width=None, height=650, center=st.session_state["map_center"], zoom=st.session_state["map_zoom"])

    # 7. LOGICA DE CLIC
    if output and output.get('last_clicked'):
        clicked_lat = output['last_clicked']['lat']
        clicked_lon = output['last_clicked']['lng']
        
        # Si la coordenada es diferente, actualizamos
        if abs(clicked_lat - st.session_state["pin_lat"]) > 0.0001:
            st.session_state["pin_lat"] = clicked_lat
            st.session_state["pin_lon"] = clicked_lon
            st.rerun()

    # 8. OBTENER DATOS GEOGRÁFICOS
    lat, lon = st.session_state["pin_lat"], st.session_state["pin_lon"]
    direccion, depto_detectado = "Cargando...", None
    
    key_geo = f"{lat}_{lon}"
    if "geo_cache" not in st.session_state: st.session_state["geo_cache"] = {}

    if key_geo in st.session_state["geo_cache"]:
        data = st.session_state["geo_cache"][key_geo]
        direccion = data['dir']
        depto_detectado = data['dep']
    else:
        try:
            geolocator = Nominatim(user_agent="sofips_v17")
            location = geolocator.reverse(f"{lat}, {lon}", zoom=10)
            if location:
                direccion = location.address
                raw = location.raw.get('address', {})
                state = raw.get('state', raw.get('region', ''))
                if state:
                    state = unidecode.unidecode(state).upper().replace("DEPARTAMENTO DE ", "").replace("REGION ", "").strip()
                depto_detectado = state
                
                st.session_state["geo_cache"][key_geo] = {'dir': direccion, 'dep': depto_detectado}
            else:
                direccion = f"{lat:.4f}, {lon:.4f}"
        except:
            direccion = "Sin conexión"

    return lat, lon, direccion, depto_detectado