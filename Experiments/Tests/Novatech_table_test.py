# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 11:19:09 2023

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")
import time

from artiq.experiment import delay, kernel, ms, EnvExperiment, us, now_mu, parallel, sequential
from NovaTechClass import _NovaTech

class NovaTech_table_test_Exp(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.nova = _NovaTech(self)
        self.setattr_device("ttl0")

    def prepare(self):

        # self.nova.set_gain(0, 0.3)
        # self.nova.set_freq(0, 0.5*1e6)
        # self.nova.set_gain(1, 0.3)
        # self.nova.set_freq(1, 0.5*1e6)

        self.nova.table_init()
        ind = 0
        for _ in range(10):

            self.nova.table_write(ind, 100, 0, 1, 1023)
            self.nova.table_write(ind+1, 100, 0, 1, 1023)
            ind += 2
        self.nova.table_start()

    @kernel
    def run(self):
        self.core.reset()
        delay(100*ms)
        self.ttl0.output()
        self.ttl0.on()

        for _ in range(10):
            self.ttl0.off()
            delay(10*us)
            self.ttl0.on()
            delay(1000*ms)


        self.ttl0.off()
