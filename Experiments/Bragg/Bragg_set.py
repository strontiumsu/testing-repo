# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 13:50:24 2023

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

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

        self.aoms_off = []
        if not self.Dipole:self.aoms_off.append('Dipole')
        if not self.Bragg1:self.aoms_off.append('Bragg1')
        if not self.Bragg2:self.aoms_off.append('Bragg2')
        if not self.Homodyne:self.aoms_off.append('Homodyne')

    def prepare(self):
        self.bragg.prepare_aoms()

    @kernel
    def run(self):
        self.core.reset()
        self.bragg.init_aoms(on=True)

        self.bragg.AOMs_on(["Bragg1", "Bragg2"])
