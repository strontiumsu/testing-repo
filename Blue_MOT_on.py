# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022

@author: sr
"""


from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461 import*


class Blue_MOT_on(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        #self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        # #self.HC=HCDL(self)
        
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        #self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        # Initialize camera
        #self.Detect.camera_init()
        #self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        self.BB.init_aoms()  # Initialize AOMs
        #self.BB.MOT_on()
        self.MC.Set_current(self.MC.Current_amplitude)
        
        
        delay(500*ms)
        #self.MC.Zero_current()    
        #self.Detect.clean_up()