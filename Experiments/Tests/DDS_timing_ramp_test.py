# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 18:41:38 2024

@author: ejporter
"""



from artiq.experiment import *
import numpy as np
from artiq.coredevice import ad9910

from BraggClass import _Bragg

class DDS_timing_test(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.bragg=_Bragg(self)
        self.setattr_device("ttl1")
        self.setattr_device("scheduler")

    def prepare(self):
        self.bragg.prepare_aoms()
        self.scan_dds = self.bragg.urukul_channels[1]

        self.f1 = 85*MHz
        self.delta_f = 30*MHz
        self.f2 = self.f1 + self.delta_f

        self.N = 1024
        self.freq_list = np.linspace(self.f1, self.f2, self.N)
        self.freq_list_ram = np.full(self.N, 1)
        self.scan_dds.frequency_to_ram(self.freq_list, self.freq_list_ram)
        self.scan_length = 300*us
        self.step_size = int(self.scan_length/(1024*4*ns))



    @kernel
    def prepare_kernel(self):

        self.ttl1.output()
        self.ttl1.off()
        delay(10*ms)
        self.scan_dds.set_cfr1(ram_enable=0)

        self.scan_dds.cpld.io_update.pulse_mu(8)
        self.scan_dds.set_profile_ram(start=0, end=self.N-1, step=(self.step_size | (2**6 - 1 ) << 16),
                                 profile=0, mode=ad9910.RAM_MODE_RAMPUP)
        self.scan_dds.cpld.set_profile(0)
        delay(10 * us)
        self.scan_dds.cpld.io_update.pulse_mu(8)
        delay(10 * us)
        self.scan_dds.write_ram(self.freq_list_ram)
        # prepare to enable ram and set frequency as target
        delay(10 * us)
        self.scan_dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=ad9910.RAM_DEST_FTW)
        delay(100*ms)





    @kernel
    def run(self):
        self.core.reset()
        self.bragg.init_aoms(on=True)
        delay(1*ms)
        self.bragg.AOMs_off(['Bragg1', "Bragg2"])

        self.prepare_kernel()

        self.bragg.AOMs_on(['Bragg1', "Bragg2"])
        self.scan_dds.cpld.io_update.pulse_mu(8)
        delay(self.scan_length)
        with parallel:
            self.ttl1.pulse(5*us)
            self.bragg.AOMs_off(['Bragg1', "Bragg2"])
        self.scan_dds.set_cfr1(ram_enable=0)
        self.scan_dds.cpld.io_update.pulse_mu(8)
