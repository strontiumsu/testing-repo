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
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING

class Phase_Sync_Test(EnvExperiment):
    
    
    def build(self): 
       
        self.setattr_device("core")
        self.setattr_device("urukul0_cpld")
        self.d0 = self.get_device("urukul0_ch0")
        self.d1 = self.get_device("urukul0_ch1")
        self.d2 = self.get_device("urukul0_ch2")
        self.d3 = self.get_device("urukul0_ch3")
        self.ttl7 = self.get_device("ttl7")
        
        self.setattr_argument("t_pulse",NumberValue(1.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale = 1e-6,
                      unit="us"),"Args")
        
        self.setattr_argument("t_wait",NumberValue(1.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale = 1e-6,
                      unit="us"),"Args")

    @kernel
    def run(self):
        self.core.break_realtime()
        self.urukul0_cpld.init()
        self.d0.init()
        self.d1.init()
        self.d2.init()
        self.d3.init()
        
        delay(2000*us)
        
            
        self.d0.set_att(15*dB)
        self.d1.set_att(15*dB)
        self.d2.set_att(15*dB)
        self.d3.set_att(15*dB)
            
        # self.d0.set(93*MHz)
        # self.d1.set(93*MHz)
        # self.d2.set(93*MHz)
        # self.d3.set(93*MHz)
        # delay(10*us)
        
        # self.d0.set_phase_mode(PHASE_MODE_ABSOLUTE)
        # self.d1.set_phase_mode(PHASE_MODE_ABSOLUTE)
        # self.d2.set_phase_mode(PHASE_MODE_ABSOLUTE)
        # self.d3.set_phase_mode(PHASE_MODE_ABSOLUTE)
        
        self.d0.set_phase_mode(PHASE_MODE_TRACKING)
        self.d1.set_phase_mode(PHASE_MODE_TRACKING)
        self.d2.set_phase_mode(PHASE_MODE_TRACKING)
        self.d3.set_phase_mode(PHASE_MODE_TRACKING)
            
        delay(10*us)
        
        self.d0.sw.off()
        self.d1.sw.off()
        self.d2.sw.off()
        self.d3.sw.off()
        self.ttl7.off()
        
        
        nreps = 100
        for ii in range(nreps):
            
            ph = ii/nreps
            
            t = now_mu()
            self.d0.set(93*MHz,phase=0.0, ref_time_mu=t)
            self.d1.set(93*MHz,phase=0.0, ref_time_mu=t)
            self.d2.set(93*MHz,phase=0.0, ref_time_mu=t)
            self.d3.set(93*MHz,phase=0.0, ref_time_mu=t)
            delay(1*ms)

            with parallel:
                #self.ttl7.on()
                self.d0.sw.on()
                self.d1.sw.on()
                self.d2.sw.on()
                self.d3.sw.on()

            with parallel:
                delay(self.t_pulse)
                #self.ttl7.off()
            
            with parallel:
                self.ttl7.on()
                self.d0.sw.off()
                self.d1.sw.off()
                self.d2.sw.off()
                self.d3.sw.off()
                
            # with parallel:
            #     if ii%2 ==0:
            #         self.d0.set(93*MHz, phase=0.5, ref_time_mu=t)
            #     else:
            #         self.d0.set(93*MHz, phase=0.0, ref_time_mu=t)
                delay(self.t_wait)

            with parallel:
                self.ttl7.off()
                self.d0.sw.on()
                self.d1.sw.on()
                self.d2.sw.on()
                self.d3.sw.on()

            with parallel:
                delay(self.t_pulse)
                #self.ttl7.off()
            
            with parallel:
                self.ttl7.on()
                self.d0.sw.off()
                self.d1.sw.off()
                self.d2.sw.off()
                self.d3.sw.off()
            
            self.ttl7.off()
 
        self.d0.sw.on()
        self.d1.sw.on()
        self.d2.sw.on()
        self.d3.sw.on()
        self.ttl7.off()
        
         
        
         