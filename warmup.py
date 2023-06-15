# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *  
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689
from ThreePhoton689Class import _ThreePhoton689 


class warmup(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        self.th_ph=_ThreePhoton689(self)
        self.setattr_device("ttl5")
        self.setattr_device("ttl6")
        
        
        self.setattr_argument("blue", BooleanValue(False))
        self.setattr_argument("red", BooleanValue(False))
        self.setattr_argument("three_photon", BooleanValue(False))
    
    def prepare(self):  
        
        # Set AOM attenuations

        self.BB.set_atten()
        self.BR.set_atten()
        self.th_ph.set_atten()
 
    def run(self):
        
        while 1:
            self.core.comm.close()
            self.scheduler.pause()
            self.safety_settings()
    
    @kernel        
    def safety_settings(self):
        self.core.reset()
        delay(100*ms)
        self.BB.init_aoms()
        self.BR.init_aoms()
        self.th_ph.init_aoms()
        
        
        if not self.blue:
            self.BB.MOT2D_off()
            self.BB.MOT_off()
            self.BB.Zeeman_off()        
            self.BB.Probe_AOM_off()
            self.BR.repumper_3P0_off()
            self.BR.repumper_3P2_off()
        if not self.red:
            self.ttl5.on() #turn off modulation channel
            self.ttl6.off() 
        if not self.three_photon:
            self.th_ph.switch1_off()
            self.th_ph.switch2_off()
            self.th_ph.switch3_off()
            
            
        if self.blue:           
            self.BB.MOT2D_on()
            self.BB.MOT_on()
            self.BB.Zeeman_on()        
            self.BB.Probe_AOM_on()
            self.BR.repumper_3P0_on()
            self.BR.repumper_3P2_on()
        if self.red:
            self.ttl5.on() #turn off modulation channel
            self.ttl6.on() 
        if self.three_photon:
            self.th_ph.switch1_on()
            self.th_ph.switch2_on()
            self.th_ph.switch3_on()
        
