# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 08:48:52 2023

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 13:17:12 2022

@author: sr
"""

from artiq.language import *

from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING
import numpy as np


class UrukulPulse(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.d0 = self.get_device("urukul1_ch0")
        self.d1 = self.get_device("urukul1_ch1")
        self.d2 = self.get_device("urukul1_ch2")
        self.d3 = self.get_device("urukul1_ch3")
        
        self.setattr_argument("pulse_duration",NumberValue(50.0*1e-3,min=0.0*1e-3,max=1000.00*1e-3,scale=1e-3,
                      unit="ms"),"Params") # ramp duration
        
        #self.setattr_argument("Npulses",NumberValue(30,min=0,max=100.00),"Params")
        self.setattr_argument("duty",NumberValue(0.5,min=0.,max=1.00),"Params")
        

    @kernel
    def run(self):
        self.core.break_realtime()
        self.d0.cpld.init()
        self.d0.init()
        self.d1.init()
        self.d2.init()
        self.d3.init()

        
        self.d0.set_att(5*dB)
        self.d1.set_att(10*dB)
        self.d2.set_att(5*dB)
        self.d3.set_att(6*dB)

        self.d0.set(90*MHz)
        self.d1.set(100*MHz)
        self.d2.set(210*MHz)
        self.d3.set(210*MHz)

        self.d0.sw.on()
        self.d1.sw.on()
        self.d2.sw.on()
        #self.d3.sw.on()
        
        for i in range(2000):
            self.d3.sw.on()
            delay(0.2*ms)
            self.d3.sw.off()
            delay(10*ms)