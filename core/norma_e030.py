import numpy as np
# CORRECCIÓN AQUÍ: Usamos ruta absoluta 'core.base...' en vez de '.base...'
from core.base_seismic_code import SeismicCode 

class NormaE030(SeismicCode):
    def __init__(self):
        super().__init__("NTE E.030 (2018/2025)", "Perú")
        # Datos del PDF (Zonas y Suelos)
        self.zonas = {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}
        self.factor_S = {
            'S0': {4: 0.80, 3: 0.80, 2: 0.80, 1: 0.80},
            'S1': {4: 1.00, 3: 1.00, 2: 1.00, 1: 1.00},
            'S2': {4: 1.05, 3: 1.15, 2: 1.20, 1: 1.20},
            'S3': {4: 1.10, 3: 1.20, 2: 1.40, 1: 1.40}
        }
        self.periodos = {
            'S0': {'TP': 0.3, 'TL': 3.0},
            'S1': {'TP': 0.4, 'TL': 2.5},
            'S2': {'TP': 0.6, 'TL': 2.0},
            'S3': {'TP': 1.0, 'TL': 1.6}
        }
        self.categorias = {'A1': 1.0, 'A2': 1.5, 'B': 1.3, 'C': 1.0} 

    def _calcular_C(self, T, TP, TL):
        if T < 0.2 * TP: return 1 + 7.5 * (T / TP)
        elif T <= TP: return 2.5
        elif T < TL: return 2.5 * (TP / T)
        else: return 2.5 * (TP * TL) / (T**2)

    def get_spectrum_curve(self, params, T_max=6.0, dt=0.01):
        if params['zona'] not in self.zonas: params['zona'] = 4
        
        Z = self.zonas[params['zona']]
        S = self.factor_S[params['suelo']][params['zona']]
        TP = self.periodos[params['suelo']]['TP']
        TL = self.periodos[params['suelo']]['TL']
        U = self.categorias[params['categoria']]
        R = params['R_coef']

        T_vals = np.arange(0, T_max + dt, dt)
        
        Sa_design = [] 
        Sa_elastic = []

        for T in T_vals:
            C = self._calcular_C(T, TP, TL)
            
            # 1. Espectro Elástico (en g puros)
            sa_el = (Z * U * C * S)
            
            # 2. Espectro de Diseño (en g puros)
            sa_des = sa_el / R
            
            Sa_elastic.append(sa_el)
            Sa_design.append(sa_des)
            
        return T_vals, np.array(Sa_design), np.array(Sa_elastic), {"Z": Z, "S": S, "TP": TP, "TL": TL, "U": U}