# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 11:19:09 2023

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")
import time

from artiq.experiment import delay, kernel, ms, EnvExperiment, us, now_mu, parallel, sequential
from NovaTechClass import _NovaTech

class NovaTech_table_test_Exp(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.nova = _NovaTech(self)
        self.setattr_device("ttl0")

    def prepare(self):

        self.dev.set_gain(0, 0.2)
        self.dev.set_freq(0, 10*1e6)

        self.dev.table_init()
        ind = 0
        for _ in range(2):
            self.dev.table_write(ind, 50, 800, 50, 1023)
            self.dev.table_write(ind+1, 0, 0, 50, 1023)
            ind += 2
        self.dev.table_start()

    @kernel
    def run(self):
        self.core.reset()
        self.ttl0.output()

        for _ in range(20):
            self.ttl0.pulse(1*ms)
            delay(200*ms)



        self.core.wait_until_mu(now_mu())
        self.dev.close()
