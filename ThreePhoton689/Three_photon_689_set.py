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


from artiq.experiment import *
import numpy as np    

from ThreePhoton689Class import _ThreePhoton689 

class Three_photon_689_set(EnvExperiment):
    
    
    def build(self): 
        self.setattr_device("core")
        self.th_ph=_ThreePhoton689(self)
        self.setattr_device("ttl0")
      
    def prepare(self):  
        
      
        self.th_ph.set_atten()
       
    @kernel    
    def run(self):
        
        self.core.reset()
        self.th_ph.init_aoms()
        self.ttl0.output()
        delay(1*ms)
        self.ttl0.on()

        
         
        
            #self.Detect.clean_up()