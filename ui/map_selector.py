import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import unidecode # Para quitar tildes (Junín -> Junin)

def mostrar_mapa_selector():
    st.markdown("### 📍 Ubicación del Proyecto")
    
    # 1. INICIALIZACIÓN
    if "pin_lat" not in st.session_state:
        st.session_state["pin_lat"] = -12.0464 # Lima
        st.session_state["pin_lon"] = -77.0428
        st.session_state["map_zoom"] = 5
        st.session_state["map_center"] = [-9.19, -75.01]

    # 2. CREACIÓN DEL MAPA
    m = folium.Map(
        location=st.session_state["map_center"], 
        zoom_start=st.session_state["map_zoom"],
        control_scale=True,
        tiles=None
    )

    # --- 3. CSS CURSOR ---
    css_cursor = """
    <style>
        .leaflet-container, .leaflet-grab, .leaflet-interactive, .leaflet-dragging .leaflet-grab {
            cursor: crosshair !important;
        }
    </style>
    """
    m.get_root().html.add_child(folium.Element(css_cursor))

    # --- 4. GAMA DE MAPAS AMPLIADA ---
    
    # A. Google Híbrido (Default)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google', name='Google Híbrido', overlay=False, control=True, show=True
    ).add_to(m)

    # B. Esri Satélite (Mejor resolución en algunas zonas, sin letras)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Esri Satélite HD', overlay=False, control=True, show=False
    ).add_to(m)

    # C. Google Terreno
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attr='Google', name='Google Terreno', overlay=False, control=True, show=False
    ).add_to(m)

    # D. Google Calles (Roadmap)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google', name='Google Calles', overlay=False, control=True, show=False
    ).add_to(m)

    # E. Carto Dark (Modo oscuro profesional)
    folium.TileLayer(
        'CartoDB dark_matter', name='Modo Oscuro', overlay=False, control=True, show=False
    ).add_to(m)

    # --- 5. CAPA E.030 ---
    geojson_url = "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_departamental_simple.geojson"

    def style_function(feature):
        dept = feature['properties']['NOMBDEP']
        opacity = 0.15 
        if dept in ['TUMBES', 'PIURA', 'LAMBAYEQUE', 'LA LIBERTAD', 'ANCASH', 'LIMA', 'CALLAO', 'ICA', 'AREQUIPA', 'MOQUEGUA', 'TACNA']:
            return {'fillColor': '#FF0000', 'color': 'white', 'weight': 0.5, 'fillOpacity': opacity}
        elif dept in ['CAJAMARCA', 'SAN MARTIN', 'HUANCAVELICA', 'AYACUCHO', 'APURIMAC', 'PASCO', 'JUNIN']:
            return {'fillColor': '#FFD700', 'color': 'white', 'weight': 0.5, 'fillOpacity': opacity}
        elif dept in ['AMAZONAS', 'HUANUCO', 'UCAYALI', 'CUSCO', 'PUNO']:
            return {'fillColor': '#228B22', 'color': 'white', 'weight': 0.5, 'fillOpacity': opacity}
        else:
            return {'fillColor': '#ADFF2F', 'color': 'white', 'weight': 0.5, 'fillOpacity': opacity}

    folium.GeoJson(
        geojson_url, name="Zonas E.030 (Colores)", style_function=style_function, overlay=True, show=True
    ).add_to(m)

    folium.LayerControl(position='topright').add_to(m)

    # 6. MARCADOR Y CARTELES
    folium.Marker([st.session_state["pin_lat"], st.session_state["pin_lon"]], icon=folium.Icon(color="red", icon="crosshairs", prefix='fa')).add_to(m)
    
    m.get_root().html.add_child(folium.Element("""
        <div style="position: fixed; top: 10px; left: 50px; width: 220px; background-color: white; border: 2px solid #d33; padding: 5px; z-index:9999; font-size:14px; text-align: center; border-radius: 5px; opacity: 0.9; cursor: default;">
            🎯 <b>Haz CLIC para ubicar</b>
        </div>
    """))

    output = st_folium(m, width=None, height=750, center=st.session_state["map_center"], zoom=st.session_state["map_zoom"])

    # 7. ACTUALIZACIÓN POSICIÓN
    lat, lon, direccion, depto_detectado = st.session_state["pin_lat"], st.session_state["pin_lon"], "Calculando...", None

    if output and output.get('last_clicked'):
        clicked_lat = output['last_clicked']['lat']
        clicked_lon = output['last_clicked']['lng']
        if clicked_lat != st.session_state["pin_lat"]:
            st.session_state["pin_lat"] = clicked_lat
            st.session_state["pin_lon"] = clicked_lon
            st.rerun()

    # 8. GEOCODING INTELIGENTE (Detectar Departamento)
    key_cache = f"{lat}_{lon}"
    if "geo_cache" not in st.session_state: st.session_state["geo_cache"] = {}

    if key_cache in st.session_state["geo_cache"]:
        data = st.session_state["geo_cache"][key_cache]
        direccion = data['dir']
        depto_detectado = data['dept']
    else:
        try:
            geolocator = Nominatim(user_agent="sofips_v15")
            location = geolocator.reverse(f"{lat}, {lon}", zoom=10)
            if location:
                direccion = location.address
                # Extraer el estado/departamento del objeto raw
                raw_addr = location.raw.get('address', {})
                state = raw_addr.get('state', raw_addr.get('region', ''))
                
                # Limpieza de texto (Quitar "Departamento de", tildes, etc.)
                if state:
                    state = unidecode.unidecode(state).upper().replace("DEPARTAMENTO DE ", "").replace("REGION ", "").strip()
                
                depto_detectado = state
                
                # Guardar en caché
                st.session_state["geo_cache"][key_cache] = {'dir': direccion, 'dept': depto_detectado}
            else:
                direccion = f"Lat: {lat:.4f}, Lon: {lon:.4f}"
        except:
            direccion = "Sin conexión"

    return lat, lon, direccion, depto_detectado