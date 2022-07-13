# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 22:17:58 2022

@author: sr
"""

from scipy import signal
from artiq.experiment import *
import numpy as np


class TriangleRamp(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.dac=self.get_device("zotino0")
        
        
    def prepare(self):
        self.period = 0.05*s
        self.sample = 64
        t = np.linspace(0, 1, self.sample)
        self.voltages = 2*signal.sawtooth(2*np.pi*t, 1.0)-2.0
        self.interval = self.period/self.sample

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        self.dac.init()
        delay(1*ms)
        counter = 0
        while True:
            self.dac.set_dac([self.voltages[counter]], [7])
            counter = (counter + 1) % self.sample
            delay(self.interval)