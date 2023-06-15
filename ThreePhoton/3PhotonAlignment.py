# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 16:08:46 2023

@author: E. Porter
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np    

from ThreePhotonClass import _ThreePhoton

class Three_photon_Align(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.ThPh = _ThreePhoton(self)
        self.t0 = np.int64(0)
             
    def prepare(self):
        self.ThPh.prepare_aoms()
     
    @kernel
    def run(self):
        self.core.reset()
        self.ThPh.init_aoms(on=False)
        delay(50*ms)
        # self.t0 = now_mu()
        # print(self.t0)
        phase = 0.0
        while True:
            # self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1 , 0.0, self.t0, 0)            
            # self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2 , 0.0, self.t0, 0)
            # self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3 , 0.0, self.t0, 0)
            self.ThPh.threePhoton_pulse(3*us)
            delay(100*ms)

