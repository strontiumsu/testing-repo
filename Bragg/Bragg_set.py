# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 13:50:24 2023

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np

from BraggClass import _Bragg

class Bragg_set(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.bragg=_Bragg(self)
        
        self.setattr_argument("Dipole", BooleanValue(False))
        self.setattr_argument("Bragg1", BooleanValue(False))
        self.setattr_argument("Bragg2", BooleanValue(False))
        self.setattr_argument("Homodyne", BooleanValue(False))
        
        self.aoms_on = []
        if self.Dipole:self.aoms_on.append('Dipole')
        if self.Bragg1:self.aoms_on.append('Bragg1')
        if self.Bragg2:self.aoms_on.append('Bragg2')
        if self.Homodyne:self.aoms_on.append('Homodyne')

    def prepare(self):
        self.bragg.prepare_aoms()

    @kernel
    def run(self):
        self.core.reset()
        self.bragg.init_aoms(on=True)
        # self.bragg.AOMs_on(self.aoms_on)
