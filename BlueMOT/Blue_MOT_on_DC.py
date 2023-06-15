# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
import numpy as np    
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689


class Blue_MOT_on_DC(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)

        self.setattr_argument("repumper_3P0_on",BooleanValue(True),"Repumpers")
        self.setattr_argument("repumper_3P2_on",BooleanValue(True),"Repumpers")
        self.setattr_argument("push_beam",BooleanValue(False),"Loading")
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()

    @kernel    
    def run(self):

        self.core.reset()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        self.BB.init_aoms()  # Initialize AOMs
        self.BR.init_aoms()
        self.BB.Probe_AOM_off()
        self.BB.MOT_on()
        
        if self.push_beam:
            self.BB.Probe_AOM_on()
        else:
            self.BB.Probe_AOM_off()
        
        # Main loop
        
        self.BR.repumper_3P0_off()
        self.BR.repumper_3P2_off()
        
        if self.repumper_3P0_on:
                self.BR.repumper_3P0_on()
                
        if self.repumper_3P2_on: 
                self.BR.repumper_3P2_on()

        self.MC.Blackman_ramp_up() # Ramp up MOT coil current
        self.MC.flat()
     