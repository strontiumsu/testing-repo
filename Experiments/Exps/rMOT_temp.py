from artiq.experiment import *
from TemperatureTemplate import _Temperature_scan__template_exp as template


class rMOT_temp(template):
    
    @kernel
    def prepare_atoms(self):
        self.MOTs.rMOT_pulse()