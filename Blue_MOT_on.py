# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022

@author: sr
"""


from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461Class import*


class Blue_MOT_on(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        #self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        self.setattr_device("ttl5")
        self.setattr_device("ttl7")
        # #self.HC=HCDL(self)
        
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        # Initialize camera
        #self.Detect.camera_init()
        #self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):

        self.core.reset()
        
        self.ttl5.on()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        self.BB.init_aoms()  # Initialize AOMs
        #self.BB.MOT_on()
        # Main loop
        for ii in range(200):
            self.MC.Blackman_ramp_up()                    # Ramp up MOT coil current
            self.MC.flat()
            self.ttl7.off()   
            self.MC.flat()                                
            self.MC.Blackman_ramp_down()
            self.ttl7.on()
            delay(self.MC.Pulse_fully_on_duration*2)

        self.ttl5.off()
        delay(500*ms)
        self.MC.Zero_current()    