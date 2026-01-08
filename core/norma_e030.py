import numpy as np
from core.base_seismic_code import SeismicCode

class NormaE030(SeismicCode):
    def __init__(self):
        super().__init__("NTE E.030 (2018/2025)", "Perú")
        
        # 1. ZONAS
        self.zonas = {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}
        
        # 2. SUELOS (Claves limpias, sin texto descriptivo)
        self.factor_S = {
            'S0': {4: 0.80, 3: 0.80, 2: 0.80, 1: 0.80},
            'S1': {4: 1.00, 3: 1.00, 2: 1.00, 1: 1.00},
            'S2': {4: 1.05, 3: 1.15, 2: 1.20, 1: 1.20},
            'S3': {4: 1.10, 3: 1.20, 2: 1.40, 1: 1.40},
            'S4': {4: None, 3: 1.30, 2: 1.70, 1: 2.40}
        }
        
        self.periodos = {
            'S0': {'TP': 0.3, 'TL': 3.0},
            'S1': {'TP': 0.4, 'TL': 2.5},
            'S2': {'TP': 0.6, 'TL': 2.0},
            'S3': {'TP': 1.0, 'TL': 1.6},
            'S4': {'TP': 1.2, 'TL': 2.0}
        }
        
        # 3. CATEGORÍAS (Claves limpias)
        self.categorias = {
            'A1': 1.0, 
            'A2': 1.5,
            'B': 1.3,
            'C': 1.0
        }
        
        # 4. SISTEMAS (Claves limpias)
        self.sistemas_estructurales = {
            'Acero (SMF)': 8,
            'Acero (IMF)': 7,
            'Acero (OMF)': 6,
            'Acero (SCBF)': 6,
            'Acero (EBF)': 8,
            'Concreto (Pórticos)': 8,
            'Concreto (Dual)': 7,
            'Concreto (Muros)': 6,
            'Concreto (Muros D.L.)': 4,
            'Albañilería': 3,
            'Madera': 7
        }

        # 5. IRREGULARIDADES
        self.irregularidad_altura = {
            'Regular (Ia=1.0)': 1.0,
            'Piso Blando': 0.75,
            'Piso Débil': 0.75,
            'Extrema Rigidez': 0.50,
            'Extrema Resistencia': 0.50,
            'Masa o Peso': 0.90,
            'Geométrica Vertical': 0.90,
            'Discontinuidad': 0.80,
            'Discontinuidad Extrema': 0.60
        }
        
        self.irregularidad_planta = {
            'Regular (Ip=1.0)': 1.0,
            'Torsional': 0.75,
            'Torsional Extrema': 0.60,
            'Esquinas Entrantes': 0.90,
            'Discontinuidad Diafragma': 0.85,
            'Sistemas no Paralelos': 0.90
        }

    def _calcular_C(self, T, TP, TL):
        if T < 0.2 * TP: return 1 + 7.5 * (T / TP)
        elif T <= TP: return 2.5
        elif T < TL: return 2.5 * (TP / T)
        else: return 2.5 * (TP * TL) / (T**2)

    def get_spectrum_curve(self, params, T_max=6.0, dt=0.01):
        if params['zona'] not in self.zonas: params['zona'] = 4
        
        Z = self.zonas[params['zona']]
        
        S_val = self.factor_S[params['suelo']][params['zona']]
        error_msg = ""
        if S_val is None:
            S = 0
            error_msg = "⚠️ Z4 + S4 requiere estudio específico."
        else:
            S = S_val

        TP = self.periodos[params['suelo']]['TP']
        TL = self.periodos[params['suelo']]['TL']
        
        U = params['u_val'] 
        Rx = params['rx_val']
        Ry = params['ry_val']

        T_vals = np.arange(0, T_max + dt, dt)
        Sa_x, Sa_y, Sa_el = [], [], []

        for T in T_vals:
            C = self._calcular_C(T, TP, TL)
            sa_el_val = (Z * U * C * S)
            Sa_el.append(sa_el_val)
            Sa_x.append(sa_el_val / Rx if Rx > 0 else 0)
            Sa_y.append(sa_el_val / Ry if Ry > 0 else 0)
            
        return T_vals, np.array(Sa_x), np.array(Sa_y), np.array(Sa_el), {
            "Z": Z, "S": S if S_val is not None else "Especial", "TP": TP, "TL": TL, "U": U, 
            "Rx": Rx, "Ry": Ry, "R0_x": params.get('r0_x', 0), "R0_y": params.get('r0_y', 0),
            "Error": error_msg
        }