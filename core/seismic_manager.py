# core/seismic_manager.py
from core.norma_e030 import NormaE030

class SeismicManager:
    def __init__(self):
        # Aquí iremos agregando las normas de otros países
        self.available_codes = {
            "Perú (NTE E.030-2025)": NormaE030,
            "Chile (NCh433) - [En Desarrollo]": None,   
            "Colombia (NSR-10) - [En Desarrollo]": None,
            "México (CFE-15) - [En Desarrollo]": None
        }

    def get_norma_class(self, selection):
        """Devuelve la CLASE de la norma seleccionada"""
        return self.available_codes.get(selection)