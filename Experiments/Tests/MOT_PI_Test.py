# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 10:03:56 2023

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

from artiq.experiment import EnvExperiment, BooleanValue, kernel, ms, NumberValue, delay, parallel, sequential, RTIOUnderflow

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera


class MOT_PID_test(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.MOTs = _Cooling(self)

    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()

    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        delay(100*ms)

        for i in range(30):
            self.MOTs.set_current(6.5)
            delay(100*ms)
            self.MOTs.set_current(0.0)
            delay(500*ms)

        self.MOTs.set_current(0.0)
