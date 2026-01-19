import pandas as pd

class LocationData:
    def __init__(self):
        try:
            self.df_deptos = pd.read_csv("core/db/departamentos.txt")
            self.df_provs = pd.read_csv("core/db/provincias.txt")
            self.df_distritos = pd.read_csv("core/db/distritos_gps.txt")
            # Limpieza
            for df in [self.df_deptos, self.df_provs, self.df_distritos]:
                for col in df.select_dtypes(['object']).columns:
                    df[col] = df[col].str.strip()
        except Exception as e:
            print(f"Error cargando DB: {e}")

    def get_departamentos(self):
        return sorted(self.df_deptos['Departamento'].tolist())

    def get_provincias(self, depto_name):
        res = self.df_deptos[self.df_deptos['Departamento'] == depto_name]
        if res.empty: return []
        depto_id = res['Id'].values[0]
        return sorted(self.df_provs[self.df_provs['Id Departamento'] == depto_id]['Provincia'].tolist())

    def get_distritos_data(self, prov_name):
        res = self.df_provs[self.df_provs['Provincia'] == prov_name]
        if res.empty: return pd.DataFrame()
        prov_id = res['Id'].values[0]
        return self.df_distritos[self.df_distritos['Id Provincia'] == prov_id]