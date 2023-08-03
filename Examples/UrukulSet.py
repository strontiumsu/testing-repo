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


class UrukulSet(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.d0 = self.get_device("urukul1_ch0")
        self.d1 = self.get_device("urukul1_ch1")
        self.d2 = self.get_device("urukul1_ch2")
        self.d3 = self.get_device("urukul1_ch3")

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
        self.d3.set_att(15*dB)

        self.d0.set(90*MHz)
        self.d1.set(100*MHz)
        self.d2.set(210*MHz)
        self.d3.set(213*MHz)

        self.d0.sw.on()
        self.d1.sw.on()
        self.d2.sw.on()
        self.d3.sw.on()