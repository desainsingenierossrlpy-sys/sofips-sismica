import pandas as pd
import os

class LocationData:
    def __init__(self):
        # Rutas a los archivos
        base_path = "core/db"
        self.file_dep = os.path.join(base_path, "departamentos.txt")
        self.file_prov = os.path.join(base_path, "provincias.txt")
        self.file_dist = os.path.join(base_path, "distritos_gps.txt")
        
        # Cargar datos en memoria (Cache)
        self.df_dep = self._load_csv(self.file_dep)
        self.df_prov = self._load_csv(self.file_prov)
        self.df_dist = self._load_csv(self.file_dist)

    def _load_csv(self, path):
        if os.path.exists(path):
            try:
                # Leemos asumiendo coma como separador y codificación utf-8
                return pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
            except:
                return pd.DataFrame()
        return pd.DataFrame()

    def get_departamentos(self):
        if self.df_dep.empty: return []
        return self.df_dep['Departamento'].tolist()

    def get_provincias(self, nombre_dep):
        if self.df_dep.empty or self.df_prov.empty: return []
        # 1. Buscar ID del Dep
        id_dep = self.df_dep[self.df_dep['Departamento'] == nombre_dep]['Id'].values[0]
        # 2. Filtrar Provincias
        filtro = self.df_prov[self.df_prov['Id Departamento'] == id_dep]
        return filtro['Provincia'].tolist()

    def get_distritos_data(self, nombre_prov):
        if self.df_prov.empty or self.df_dist.empty: return []
        # 1. Buscar ID Prov
        id_prov = self.df_prov[self.df_prov['Provincia'] == nombre_prov]['Id'].values[0]
        # 2. Filtrar Distritos
        filtro = self.df_dist[self.df_dist['Id Provincia'] == id_prov]
        # Retornamos el DataFrame filtrado para sacar lat/lon/zona después
        return filtro