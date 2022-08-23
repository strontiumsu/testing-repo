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



from artiq.experiment import *
import numpy as np    
from ThreePhoton689Class import* 

class Three_photon_test(EnvExperiment):
    
    
    def build(self): 
        self.setattr_device("core")
        self.th_ph=ThreePhoton689(self)
      
    def prepare(self):  
        
      
        self.th_ph.set_atten()
       
    @kernel    
    def run(self):
        
        self.core.reset()
        self.th_ph.init_aoms()

        
         
        
            #self.Detect.clean_up()