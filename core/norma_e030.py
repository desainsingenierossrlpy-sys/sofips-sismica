import numpy as np
from core.base_seismic_code import SeismicCode

class NormaE030(SeismicCode):
    def __init__(self):
        super().__init__("NTE E.030 (2018/2025)", "Perú")
        
        # 1. ZONAS (Tabla N° 1)
        self.zonas = {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}
        
        # 2. SUELOS (Tabla N° 3 y 4)
        self.factor_S = {
            'S0: Roca Dura': {4: 0.80, 3: 0.80, 2: 0.80, 1: 0.80},
            'S1: Roca o Suelos Muy Rígidos': {4: 1.00, 3: 1.00, 2: 1.00, 1: 1.00},
            'S2: Suelos Intermedios': {4: 1.05, 3: 1.15, 2: 1.20, 1: 1.20},
            'S3: Suelos Blandos': {4: 1.10, 3: 1.20, 2: 1.40, 1: 1.40},
            'S4: Condiciones Excepcionales': {4: None, 3: 1.30, 2: 1.70, 1: 2.40}
        }
        
        # Periodos (Tabla N° 4)
        self.periodos = {
            'S0: Roca Dura': {'TP': 0.3, 'TL': 3.0},
            'S1: Roca o Suelos Muy Rígidos': {'TP': 0.4, 'TL': 2.5},
            'S2: Suelos Intermedios': {'TP': 0.6, 'TL': 2.0},
            'S3: Suelos Blandos': {'TP': 1.0, 'TL': 1.6},
            'S4: Condiciones Excepcionales': {'TP': 1.2, 'TL': 2.0} # Referencial
        }
        
        # 3. CATEGORÍAS (Tabla N° 5) - Descripciones completas
        self.categorias = {
            'A1: Establecimientos de Salud (Aislamiento)': 1.0, 
            'A2: Edificaciones Esenciales': 1.5,
            'B: Edificaciones Importantes': 1.3,
            'C: Edificaciones Comunes': 1.0
        }
        
        # 4. SISTEMAS ESTRUCTURALES (Tabla N° 6) - R0 Básico
        self.sistemas_estructurales = {
            'Acero - Pórticos Especiales (SMF)': 8,
            'Acero - Pórticos Intermedios (IMF)': 7,
            'Acero - Pórticos Ordinarios (OMF)': 6,
            'Acero - EBF (Excéntricamente Arriostrados)': 8,
            'Acero - SCBF (Concéntricamente Arriostrados)': 6,
            'Concreto Armado - Pórticos': 8,
            'Concreto Armado - Dual': 7,
            'Concreto Armado - Muros Estructurales': 6,
            'Concreto Armado - Muros de Ductilidad Limitada': 4,
            'Albañilería Armada o Confinada': 3,
            'Madera': 7
        }

        # 5. FACTORES DE IRREGULARIDAD (Tablas N° 8 y 9)
        self.irregularidad_altura = {
            'Regular': 1.0,
            'Irregularidad de Rigidez (Piso Blando)': 0.75,
            'Irregularidad de Resistencia (Piso Débil)': 0.75,
            'Irregularidad Extrema de Rigidez': 0.50,
            'Irregularidad Extrema de Resistencia': 0.50,
            'Irregularidad de Masa o Peso': 0.90,
            'Irregularidad Geométrica Vertical': 0.90,
            'Discontinuidad en los Sistemas Resistentes': 0.80,
            'Discontinuidad Extrema': 0.60
        }
        
        self.irregularidad_planta = {
            'Regular': 1.0,
            'Irregularidad Torsional': 0.75,
            'Irregularidad Torsional Extrema': 0.60,
            'Esquinas Entrantes': 0.90,
            'Discontinuidad del Diafragma': 0.85,
            'Sistemas No Paralelos': 0.90
        }

    def _calcular_C(self, T, TP, TL):
        if T < 0.2 * TP: return 1 + 7.5 * (T / TP)
        elif T <= TP: return 2.5
        elif T < TL: return 2.5 * (TP / T)
        else: return 2.5 * (TP * TL) / (T**2)

    def get_spectrum_curve(self, params, T_max=6.0, dt=0.01):
        if params['zona'] not in self.zonas: params['zona'] = 4
        
        Z = self.zonas[params['zona']]
        
        # Manejo S4
        S_val = self.factor_S[params['suelo']][params['zona']]
        error_msg = ""
        if S_val is None:
            S = 0
            error_msg = "⚠️ Z4 + S4 requiere estudio específico."
        else:
            S = S_val

        TP = self.periodos[params['suelo']]['TP']
        TL = self.periodos[params['suelo']]['TL']
        
        # Recuperar U desde el nombre largo
        U = self.categorias[params['categoria']]
        
        # Recuperar R0 y calcular R final
        # R = R0 * Ia * Ip
        R0_x = self.sistemas_estructurales[params['sistema_x']]
        R0_y = self.sistemas_estructurales[params['sistema_y']]
        
        Ia_x = self.irregularidad_altura[params['ia_x']]
        Ip_x = self.irregularidad_planta[params['ip_x']]
        
        Ia_y = self.irregularidad_altura[params['ia_y']]
        Ip_y = self.irregularidad_planta[params['ip_y']]
        
        Rx = R0_x * Ia_x * Ip_x
        Ry = R0_y * Ia_y * Ip_y

        T_vals = np.arange(0, T_max + dt, dt)
        Sa_x, Sa_y, Sa_el = [], [], []

        for T in T_vals:
            C = self._calcular_C(T, TP, TL)
            val_el = (Z * U * C * S) # Elástico
            Sa_el.append(val_el)
            Sa_x.append(val_el / Rx)
            Sa_y.append(val_el / Ry)

        # Retornamos los diccionarios completos para el reporte
        info_calc = {
            "Z": Z, "S": S, "TP": TP, "TL": TL, "U": U, 
            "Rx": Rx, "Ry": Ry, "R0_x": R0_x, "R0_y": R0_y,
            "Error": error_msg
        }

        return T_vals, np.array(Sa_x), np.array(Sa_y), np.array(Sa_el), info_calc