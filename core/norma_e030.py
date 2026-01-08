import numpy as np
from core.base_seismic_code import SeismicCode

class NormaE030(SeismicCode):
    def __init__(self):
        super().__init__("NTE E.030 (2018/2025)", "Perú")
        
        self.zonas = {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}
        
        self.factor_S = {
            'S0: Roca Dura': {4: 0.80, 3: 0.80, 2: 0.80, 1: 0.80},
            'S1: Roca o Suelos Muy Rígidos': {4: 1.00, 3: 1.00, 2: 1.00, 1: 1.00},
            'S2: Suelos Intermedios': {4: 1.05, 3: 1.15, 2: 1.20, 1: 1.20},
            'S3: Suelos Blandos': {4: 1.10, 3: 1.20, 2: 1.40, 1: 1.40},
            'S4: Condiciones Excepcionales': {4: None, 3: 1.30, 2: 1.70, 1: 2.40}
        }
        
        self.periodos = {
            'S0: Roca Dura': {'TP': 0.3, 'TL': 3.0},
            'S1: Roca o Suelos Muy Rígidos': {'TP': 0.4, 'TL': 2.5},
            'S2: Suelos Intermedios': {'TP': 0.6, 'TL': 2.0},
            'S3: Suelos Blandos': {'TP': 1.0, 'TL': 1.6},
            'S4: Condiciones Excepcionales': {'TP': 1.2, 'TL': 2.0}
        }
        
        # --- TABLA N° 5: CATEGORÍA DE LAS EDIFICACIONES ---
        self.categorias = {
            'A1: Establecimientos de salud Sector Salud (2do y 3er nivel)': 1.0, # Con aislamiento
            'A1: Aislamiento Sísmico (Base)': 1.0,
            'A2: Edificaciones Esenciales (Hospitales, Policia, Bomberos, Colegios)': 1.5,
            'B: Edificaciones Importantes (Cines, Teatros, Estadios, Museos)': 1.3,
            'C: Edificaciones Comunes (Viviendas, Oficinas, Hoteles)': 1.0
        }
        
        # --- TABLA N° 6: SISTEMAS ESTRUCTURALES (R0) ---
        self.sistemas_estructurales = {
            'Acero: Pórticos Especiales Resistentes a Momentos (SMF)': 8,
            'Acero: Pórticos Intermedios Resistentes a Momentos (IMF)': 5,
            'Acero: Pórticos Ordinarios Resistentes a Momentos (OMF)': 4,
            'Acero: Pórticos Especiales Concéntricamente Arriostrados (SCBF)': 7,
            'Acero: Pórticos Ordinarios Concéntricamente Arriostrados (OCBF)': 4,
            'Acero: Pórticos Excéntricamente Arriostrados (EBF)': 8,
            'Concreto: Pórticos': 8,
            'Concreto: Dual': 7,
            'Concreto: De muros estructurales': 6,
            'Concreto: Muros de ductilidad limitada': 4,
            'Albañilería Armada o Confinada': 3,
            'Madera': 7
        }

        # --- TABLAS N° 8 y 9: IRREGULARIDADES (Ia, Ip) ---
        self.irregularidad_altura = {
            'Regular': 1.0,
            'Irregularidad de Rigidez – Piso Blando': 0.75,
            'Irregularidad de Resistencia – Piso Débil': 0.75,
            'Irregularidad Extrema de Rigidez': 0.50,
            'Irregularidad Extrema de Resistencia': 0.50,
            'Irregularidad de Masa o Peso': 0.90,
            'Irregularidad Geométrica Vertical': 0.90,
            'Discontinuidad en los Sistemas Resistentes': 0.80,
            'Discontinuidad Extrema de los Sistemas Resistentes': 0.60
        }
        
        self.irregularidad_planta = {
            'Regular': 1.0,
            'Irregularidad Torsional': 0.75,
            'Irregularidad Torsional Extrema': 0.60,
            'Esquinas Entrantes': 0.90,
            'Discontinuidad del Diafragma': 0.85,
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
        
        # AQUI LA MAGIA: Usamos los valores numéricos que vienen del Main (ya sean manuales o automáticos)
        U = params['u_val'] 
        Rx = params['rx_val']
        Ry = params['ry_val']

        T_vals = np.arange(0, T_max + dt, dt)
        Sa_x, Sa_y, Sa_el = [], [], []

        for T in T_vals:
            C = self._calcular_C(T, TP, TL)
            sa_el_val = (Z * U * C * S)
            Sa_el.append(sa_el_val)
            Sa_x.append(sa_el_val / Rx)
            Sa_y.append(sa_el_val / Ry)
            
        return T_vals, np.array(Sa_x), np.array(Sa_y), np.array(Sa_el), {
            "Z": Z, "S": S_report if S_val is None else S, "TP": TP, "TL": TL, "U": U, 
            "Rx": Rx, "Ry": Ry, 
            "Error": error_msg
        }

    @property
    def factor_S_keys(self): return list(self.factor_S.keys())
    @property
    def categorias_keys(self): return list(self.categorias.keys())
    @property
    def sistemas_keys(self): return list(self.sistemas_estructurales.keys())
    @property
    def ia_keys(self): return list(self.irregularidad_altura.keys())
    @property
    def ip_keys(self): return list(self.irregularidad_planta.keys())