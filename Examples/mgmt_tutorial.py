# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 13:48:04 2021

@author: sr
"""

from artiq.experiment import *


class MgmtTutorial(EnvExperiment):
    """Management tutorial"""
    def build(self):
     self.setattr_argument("count", NumberValue(ndecimals=0, step=1))
     self.setattr_device("ttl5")


    def run(self):
     for i in range(self.count):
        print("Hello World", i)
      