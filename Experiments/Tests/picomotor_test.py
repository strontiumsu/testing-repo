# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 17:19:36 2023

@author: sr
"""
import time

from artiq.experiment import delay, kernel, ms, EnvExperiment, us, now_mu, parallel, sequential
from PicomotorClass import _Picomotor

class Picomotor_test(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.Pico = _Picomotor(self)
        self.setattr_device("ttl4")

    def prepare(self):

        # self.Pico.set_home(1)
        self.Pico.set_position(1, 10)

    @kernel
    def run(self):
        self.core.reset()
