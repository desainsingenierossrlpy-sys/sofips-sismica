import numpy as np
from core.base_seismic_code import SeismicCode

class NormaE030(SeismicCode):
    def __init__(self):
        super().__init__("NTE E.030 (2018/2025)", "Perú")
        
        # Tabla N° 1: Factor de Zona (Z)
        self.zonas = {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}
        
        # Tabla N° 4: Factor de Suelo (S) - ACTUALIZADO CON S4
        # Nota: Z4 + S4 requiere estudio especial (valor None o 0 referencial)
        self.factor_S = {
            'S0': {4: 0.80, 3: 0.80, 2: 0.80, 1: 0.80},
            'S1': {4: 1.00, 3: 1.00, 2: 1.00, 1: 1.00},
            'S2': {4: 1.05, 3: 1.15, 2: 1.20, 1: 1.20},
            'S3': {4: 1.10, 3: 1.20, 2: 1.40, 1: 1.40},
            'S4': {4: None, 3: 1.30, 2: 1.70, 1: 2.40} # <--- NUEVO
        }
        
        # Tabla N° 5: Periodos TP y TL - ACTUALIZADO CON S4
        self.periodos = {
            'S0': {'TP': 0.3, 'TL': 3.0},
            'S1': {'TP': 0.4, 'TL': 2.5},
            'S2': {'TP': 0.6, 'TL': 2.0},
            'S3': {'TP': 1.0, 'TL': 1.6},
            'S4': {'TP': 1.2, 'TL': 2.0} # <--- NUEVO
        }
        
        # Tabla N° 7: Categoría
        self.categorias = {'A1': 1.0, 'A2': 1.5, 'B': 1.3, 'C': 1.0} 

    def _calcular_C(self, T, TP, TL):
        # Tabla N° 6
        if T < 0.2 * TP: return 1 + 7.5 * (T / TP)
        elif T <= TP: return 2.5
        elif T < TL: return 2.5 * (TP / T)
        else: return 2.5 * (TP * TL) / (T**2)

    def get_spectrum_curve(self, params, T_max=6.0, dt=0.01):
        if params['zona'] not in self.zonas: params['zona'] = 4
        
        Z = self.zonas[params['zona']]
        
        # Manejo especial para S4 en Zona 4
        S_val = self.factor_S[params['suelo']][params['zona']]
        
        # Si es el caso especial (Z4 + S4), devolvemos error controlado
        error_msg = ""
        if S_val is None:
            S = 0 # Valor dummy para no romper matemáticas
            error_msg = "⚠️ La Norma E.030 indica que para Zona 4 y Suelo S4 se requiere un Análisis de Respuesta de Sitio específico. No se puede generar espectro estándar."
        else:
            S = S_val

        TP = self.periodos[params['suelo']]['TP']
        TL = self.periodos[params['suelo']]['TL']
        U = self.categorias[params['categoria']]
        R = params['R_coef']

        T_vals = np.arange(0, T_max + dt, dt)
        
        Sa_design = [] 
        Sa_elastic = []

        for T in T_vals:
            C = self._calcular_C(T, TP, TL)
            
            # Fórmulas
            sa_el = (Z * U * C * S)
            sa_des = sa_el / R
            
            Sa_elastic.append(sa_el)
            Sa_design.append(sa_des)
        
        # Retornamos S como texto si era None para que se vea en el reporte
        S_report = "Especial" if S_val is None else S

        return T_vals, np.array(Sa_design), np.array(Sa_elastic), {
            "Z": Z, "S": S_report, "TP": TP, "TL": TL, "U": U, "Error": error_msg
        }