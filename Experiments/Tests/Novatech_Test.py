# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 09:32:14 2023

@author: sr
"""
import time

from artiq.experiment import delay, kernel, ms, EnvExperiment, us, now_mu, parallel, sequential, NumberValue


class NovaTech_Test_Exp(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("ttl4")



    @kernel
    def run(self):
        self.core.reset()
        delay(1000*ms)
        for _ in range(100):
            delay(5000*ms)
            self.ttl4.on()
            delay(5*ms)
            self.ttl4.off()
