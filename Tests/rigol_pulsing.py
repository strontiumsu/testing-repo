# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 14:24:08 2024

@author: ejporter
"""

from artiq.experiment import *

# imports
import numpy as np
import pyvisa
from time import sleep


class rigol_pulsing_exp(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("ttl1")
        rm = pyvisa.ResourceManager()
        self.rigol = rm.open_resource('USB0::0x1AB1::0x0643::DG9A241800105::INSTR') 
        
        
        self.setattr_argument("pulse_length",
            Scannable(default=[RangeScan(1.0*1e-6,30.0*1e-6,50, randomize=False),NoScan(1*1e-6)],scale=1e-6,
                      unit="us"))
        
        # self.vals = list(self.pulse_length)
        
    def prepare(self):
        assert self.rigol.query('*IDN?') =="Rigol Technologies,DG952,DG9A241800105,00.02.06.00.01 \n" 
        self.rigol.write(":SOUR1:FUNC:PULS:PER 1E-3")
        self.rigol.write(":SOUR1:BURS ON")
        self.rigol.write(":SOUR1:BURS:MODE TRIG")
        self.rigol.write(":SOUR1:BURS:NCYC 1 ")
        self.rigol.write(":SOUR1:BURS:TRIG:SOUR EXT")
        self.rigol.write(":SOUR1:BURS:TDEL 0")
        self.rigol.write(":OUTP1 ON ")

   
    def run(self):
        for val in self.pulse_length:
            self.rigol.write(f":SOUR1:FUNC:PULS:PER {val}")
            self.exp_pulse()
            print(val)
        
    @kernel    
    def exp_pulse(self):
        self.core.reset()
        self.ttl1.pulse(10*ms)
        delay(1000*ms)

        self.core.wait_until_mu(now_mu())
            
