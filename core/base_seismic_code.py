from abc import ABC, abstractmethod
import numpy as np

class SeismicCode(ABC):
    """
    CLASE MAESTRA (Plantilla)
    Todas las normas (E.030, NCh433, etc.) usarán este molde.
    """
    def __init__(self, name, country):
        self.name = name
        self.country = country

    @abstractmethod
    def get_spectrum_curve(self, params, T_max=6.0, dt=0.01):
        pass