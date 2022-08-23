# -*- coding: utf-8 -*-
"""
Created on Sat Jul  9 12:04:05 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 21:19:34 2022

@author: sr
"""



from artiq.experiment import *
import numpy as np    
from artiq.language import *
from artiq.coredevice.ad9910 import PHASE_MODE_ABSOLUTE

class Phase_Sync_Test(EnvExperiment):
    
    
    def build(self): 
       
        self.setattr_device("core")
        self.d0 = self.get_device("urukul0_ch0")
        self.d1 = self.get_device("urukul0_ch1")
        self.d2 = self.get_device("urukul0_ch2")
        self.d3 = self.get_device("urukul0_ch3")
        self.t = self.get_device("ttl6")

    @kernel
    def run(self):
        self.core.break_realtime()
        self.d0.cpld.init()
        self.d0.init()
        self.d1.init()
        self.d2.init()
        self.d3.init()
        
        for ii in range(10000):
            
            
            delay(2000*us)
            self.d0.sw.off()
            self.d1.sw.off()
            self.d2.sw.off()
            self.d3.sw.off()
            
            self.d0.set_att(25*dB)
            self.d1.set_att(25*dB)
            self.d2.set_att(25*dB)
            self.d3.set_att(25*dB)
            
            self.d0.set(95*MHz)
            self.d1.set(80*MHz)
            self.d2.set(50*MHz)
            self.d3.set(65*MHz)
            delay(10*us)
            
           
            
            self.d0.set_phase_mode(PHASE_MODE_ABSOLUTE)
            self.d1.set_phase_mode(PHASE_MODE_ABSOLUTE)
            self.d2.set_phase_mode(PHASE_MODE_ABSOLUTE)
            self.d3.set_phase_mode(PHASE_MODE_ABSOLUTE)
            
            delay(10*us)
    
            t = now_mu()
            self.d0.set(50*MHz, phase=0., ref_time_mu=t)
            self.d1.set(50*MHz, phase=.0, ref_time_mu=t)
            self.d2.set(50*MHz, phase=.0, ref_time_mu=t)
            self.d3.set(50*MHz, phase=.0, ref_time_mu=t)
    
            self.t.on()
            self.d0.sw.on()
            self.d1.sw.on()
            self.d2.sw.on()
            self.d3.sw.on()
            delay(50*ns)
            self.t.off()
            
            
            delay(10*us)
    
            t = now_mu()
            self.d0.set(50*MHz, phase=0., ref_time_mu=t)
            self.d1.set(50*MHz, phase=.0, ref_time_mu=t)
            self.d2.set(50*MHz, phase=.25, ref_time_mu=t)
            self.d3.set(50*MHz, phase=.0, ref_time_mu=t)
            
            
            delay(10*us)
            
            t = now_mu()
            self.d0.set(50*MHz, phase=0., ref_time_mu=t)
            self.d1.set(50*MHz, phase=.0, ref_time_mu=t)
            self.d2.set(50*MHz, phase=.0, ref_time_mu=t)
            self.d3.set(50*MHz, phase=.0, ref_time_mu=t)
 

        
         
        
         