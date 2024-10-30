# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 15:20:37 2024

@author: ejporter
"""
from artiq.coredevice.ad9910 import (
    RAM_DEST_FTW, RAM_MODE_RAMPUP)



from artiq.experiment import *
from artiq.coredevice import ad9910
import numpy as np



class DDS_freq_ramp_test_exp(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl1") # used for measure the delay time of DDS setting
        self.setattr_device("scheduler")
        self.setattr_device('urukul0_cpld')
        self.dds = self.get_device("urukul0_ch3")
    def prepare(self):
        # prepare frequency array
        self.N = 1024
        freq1 = np.linspace(101e6,99e6,self.N)
        self.data1 =np.full(self.N,1)
        self.dds.frequency_to_ram(freq1,self.data1)
        # prepare time step array

        self.steps = np.array([2**6])


    @kernel
    def run(self):
        self.core.break_realtime()
        self.urukul0_cpld.init()
        self.dds.init()
        self.ttl1.output()
        self.dds.sw.off()
        self.dds.set_amplitude(1.0)
        self.dds.set_att(5.0)
        for t in range(len(self.steps)):
            self.run_ram(self.steps[t])


    @kernel
    def run_ram(self, timestep_mu):
        # prepare ram
        delay(5 * us)
        self.dds.set_cfr1(ram_enable=0)
        self.dds.cpld.io_update.pulse_mu(8)
        self.dds.set_profile_ram(start=0, end=self.N-1, step=(timestep_mu | (2**6 - 1 ) << 16),
                                 profile=0, mode=ad9910.RAM_MODE_RAMPUP)
        self.dds.cpld.set_profile(0)
        delay(10 * us)
        self.dds.cpld.io_update.pulse_mu(8)
        delay(10 * us)
        self.dds.write_ram(self.data1)
        # prepare to enable ram and set frequency as target
        delay(10 * us)
        self.dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=RAM_DEST_FTW)
        # sent trigger and ramp for 1ms
        self.ttl1.pulse(5 * us)
        self.dds.sw.on()
        self.dds.cpld.io_update.pulse_mu(8)
        delay(250 * us)
        self.dds.set_cfr1(ram_enable=0)
        self.dds.sw.off()
