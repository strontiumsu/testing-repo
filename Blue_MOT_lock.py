# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 20:00:49 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461 import*
from HCDL import* 

class Blue_MOT_lock(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.HC=HCDL(self)
    
    def prepare(self):  
        
        self.HC.set_atten()
        
    
    @kernel    
    def run(self):
        
        self.core.reset()
        self.HC.init_aoms()