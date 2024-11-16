# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 16:42:13 2024

@author: ejporter
"""

from artiq import *
from DDS_Class import _DDS_Class

class _test_dds_class(_DDS_Class):
    
    def build(self):
        
        urukul = 'urukul0'
        AOMs = ["Sideband", 'Push', 'AI1', "AI2"]
        scales = [0.8, 0.8, 0.8, 0.8]
        attens = [10.0, 10.0, 10.0, 10.0]
        freqs = [4.0, 80.0, 80.0, 80.0]
        
        self.super.build(urukul, AOMs, scales, attens, freqs)
        

        
        

