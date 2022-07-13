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
from Beamline689Class import*


class Blue_MOT_on(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        #self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        self.setattr_device("ttl5")
        self.setattr_device("ttl7")
        self.BR=Beamline689(self)
        # #self.HC=HCDL(self)
        
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
        # Initialize camera
        #self.Detect.camera_init()
        #self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):

        self.core.reset()
        #self.ttl5.off()
        #self.ttl5.on()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        self.BB.init_aoms()  # Initialize AOMs
        self.BR.init_aoms()
        self.BB.MOT_on()
        # Main loop
        self.BR.repumper_3P0_on()
        self.BR.repumper_3P2_on()
        for ii in range(2):
            
            #self.BR.Red_MOT_aom_off()
            
            
            self.MC.Blackman_ramp_up()                    # Ramp up MOT coil current
            #self.BB.MOT_on()
            #delay(50*ms)
            
            #ramp down the laser intensity
            #for jj in range(500):
            #    self.BB.set_MOT3DDP_aom_atten(6.0+3*float(jj/500))
            #    delay(1*ms)
            self.MC.flat()
            
            
            #self.BR.Red_MOT_aom_on()
            #self.ttl7.off()   
            #self.MC.flat()
            #self.BR.Red_MOT_aom_off()
            #delay(50*ms)
            
            #ramp dow the MOT field
            #self.MC.Linear_ramp(3.,5.,500*ms,30)
            
            #self.MC.flat()
            #self.BB.MOT_off()
            self.MC.Zero_current()
            
            # delay(2*ms)
            # self.BB.MOT_on()
            # delay(.1*ms)
            # self.BB.MOT_off()
            #self.MC.Blackman_ramp_down_from_to(2.3,0.)                        
            #self.MC.Blackman_ramp_down()
            #self.ttl7.on()
            delay(self.MC.Pulse_fully_on_duration*2)

        self.ttl5.off()
        delay(500*ms)
        self.MC.Zero_current()    