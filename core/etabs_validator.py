import pandas as pd

class EtabsValidator:
    def __init__(self, uploaded_file):
        self.file = uploaded_file
        self.df_drifts = None
        
    def cargar_datos(self):
        """Intenta leer las pestañas del Excel de ETABS"""
        try:
            # Leemos el Excel completo
            xls = pd.ExcelFile(self.file)
            
            # Buscamos pestañas que contengan "Drift" o "Deriva"
            # ETABS en inglés suele usar "Story Drifts"
            sheet_drifts = [s for s in xls.sheet_names if "Drift" in s or "Deriva" in s]
            
            if sheet_drifts:
                # Leemos la primera hoja coincidente
                self.df_drifts = pd.read_excel(xls, sheet_drifts[0])
                
                # Limpieza básica: Eliminar filas vacías
                self.df_drifts = self.df_drifts.dropna(how='all') 
                
                # Estandarizar nombres de columnas (quitar espacios extraños)
                self.df_drifts.columns = [str(c).strip() for c in self.df_drifts.columns]
                
                return True, f"✅ Pestaña detectada: '{sheet_drifts[0]}'"
            else:
                return False, "❌ No se encontró una pestaña de 'Story Drifts' o 'Derivas' en el Excel."
                
        except Exception as e:
            return False, f"Error leyendo el archivo: {str(e)}"

    def verificar_derivas(self, limite):
        """
        Analiza las derivas y verifica cumplimiento.
        Retorna un diccionario con el diagnóstico.
        """
        if self.df_drifts is None:
            return {"status": "Error", "msg": "No hay datos cargados."}

        # Buscamos la columna que tenga los valores de deriva
        # Usualmente 'Drift', 'Max Drift', 'Deriva', etc.
        col_drift = [c for c in self.df_drifts.columns if "Drift" in c or "Deriva" in c]
        
        if not col_drift:
            return {"status": "Error", "msg": "No encontré la columna de valores de Drift en la tabla."}
        
        target_col = col_drift[0] # Usamos la primera columna que parezca ser la deriva
        
        # Convertimos a numérico por si acaso hay texto sucio
        series_drift = pd.to_numeric(self.df_drifts[target_col], errors='coerce').dropna()
        
        if series_drift.empty:
             return {"status": "Error", "msg": "La columna de Drift está vacía o no tiene números."}

        # Obtenemos el máximo absoluto
        max_drift = series_drift.abs().max()
        
        # Buscamos en qué piso ocurrió el máximo
        idx_max = series_drift.abs().idxmax()
        piso = "Desconocido"
        
        # Intentamos encontrar la columna del piso (Story, Piso, Label)
        col_piso = [c for c in self.df_drifts.columns if "Story" in c or "Piso" in c or "Label" in c]
        if col_piso:
            piso = self.df_drifts.loc[idx_max, col_piso[0]]

        # Veredicto Final
        cumple = max_drift <= limite
        
        return {
            "status": "OK" if cumple else "Falla",
            "max_val": max_drift,
            "limite": limite,
            "columna": target_col,
            "piso_critico": piso,
            "msg": ""
        }