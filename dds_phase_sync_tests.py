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
        self.d0 = self.get_device("urukul0_ch0")
        self.d1 = self.get_device("urukul0_ch1")
        self.d2 = self.get_device("urukul0_ch2")
        self.d3 = self.get_device("urukul0_ch3")
        self.t = self.get_device("ttl4")

    @kernel
    def run(self):
        self.core.break_realtime()
        self.d0.cpld.init()
        self.d0.init()
        self.d1.init()
        self.d2.init()
        self.d3.init()
        
        self.d0.set_phase_mode(PHASE_MODE_TRACKING)
        self.d1.set_phase_mode(PHASE_MODE_TRACKING)
        self.d2.set_phase_mode(PHASE_MODE_TRACKING)
        self.d3.set_phase_mode(PHASE_MODE_TRACKING)

        self.d0.set_att(10*dB)
        self.d1.set_att(10*dB)
        self.d2.set_att(10*dB)
        self.d3.set_att(10*dB)

        t = now_mu()
        self.d0.set(50*MHz, phase=0., ref_time=t)
        self.d1.set(50*MHz, phase=.5, ref_time=t)
        self.d2.set(50*MHz, phase=.25, ref_time=t)
        self.d3.set(50*MHz, phase=.75, ref_time=t)

        self.t.on()
        self.d0.sw.on()
        self.d1.sw.on()
        self.d2.sw.on()
        self.d3.sw.on()
 

        
         
        
            #self.Detect.clean_up()