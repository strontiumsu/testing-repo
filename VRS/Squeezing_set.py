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


import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")
from artiq.experiment import EnvExperiment, kernel
from SqueezingClass import _Squeezing

class Squeezing_set(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.sq=_Squeezing(self)

    def prepare(self):
        self.sq.prepare_aoms()

    @kernel
    def run(self):
        self.core.reset()
        self.sq.init_aoms(on=False)
        self.sq.AOMs_on(self.sq.AOMs)
