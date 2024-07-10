# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 16:18:04 2024

@author: ejporter
"""


import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, BooleanValue, kernel, now_mu, us, ms, NumberValue, delay, parallel, sequential

# imports
import numpy as np
import pyvisa
from BraggClass import _Bragg


class Bragg_pulse_shaping_exp(EnvExperiment):
 
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.Bragg = _Bragg(self) 
        self.setattr_device("ttl1")
        
        self.rigol= None
        self.ind = 0

        
        
        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=1000), "parameters")
        self.setattr_argument("pulse_time", NumberValue(1*1e-3,min=0.0*1e-3,max=5000.00*1e-3,scale=1e-3,
               unit="ms"),"parameters")
        self.setattr_argument("shot_time", NumberValue(1500*1e-3,min=0.0*1e-3,max=5000.00*1e-3,scale=1e-3,
               unit="ms"),"parameters")
        self.setattr_argument("arm1",BooleanValue(True),"parameters")
        self.setattr_argument("arm2",BooleanValue(True),"parameters")
        self.setattr_argument("pulse_shape",BooleanValue(True),"parameters")
        
        self.setattr_argument("amplitude", NumberValue(0.8,min=0.0,max=1.2,scale=1,
               unit="V", ndecimals = 3),"parameters")
        self.setattr_argument("phase", NumberValue(135.0,min=0.0,max=359.9,scale=1),"parameters")
    
    def prepare(self):
        self.Bragg.prepare_aoms()
        self.arms = []
        if self.arm1: self.arms.append('Bragg1')
        if self.arm2: self.arms.append('Bragg2')
        self.prepare_rigol()
        
    @kernel 
    def run(self):
        self.core.reset()
        self.ttl1.output()
        self.core.wait_until_mu(now_mu())
        self.core.reset()

        # intial as on to keep lattice on/locked
        self.Bragg.init_aoms(on=True)
        self.Bragg.AOMs_off(["Bragg2", "Bragg1"]) # make sure theyre settled thermally
        delay(1000*ms)
        
        
        for _ in range(int(self.pulses)):
            with parallel:
                self.ttl1.pulse(self.pulse_time) # triggers function gen/ turns on lock
                with sequential: # pulses the AOMs on        
                    self.Bragg.AOMs_on(self.arms)
                    delay(self.pulse_time*1.2)
                    self.Bragg.AOMs_off(self.arms)
            delay(self.shot_time)
        
    def prepare_rigol(self):
        
        #connect to device
        rm = pyvisa.ResourceManager()
        self.rigol = rm.open_resource('USB0::0x1AB1::0x0643::DG9A241800105::INSTR') 
        assert self.rigol.query('*IDN?') =="Rigol Technologies,DG952,DG9A241800105,00.02.06.00.01 \n"
        
        # turn on and set arb values
        self.rigol.write(f":SOUR1:APPL:USER {1/(3.12*self.pulse_time)},{self.amplitude},{self.amplitude/2},{self.phase}")
        self.rigol.write(":SOUR1:FUNC GAUSSPULSE")
        
        # setup burst parameters
        self.rigol.write(":SOUR1:BURS ON")
        self.rigol.write(":SOUR1:BURS:MODE TRIG")
        self.rigol.write(":SOUR1:BURS:NCYC 1 ")
        self.rigol.write(":SOUR1:BURS:TRIG:SOUR EXT")
        self.rigol.write(":SOUR1:BURS:TDEL 0")
        idle = "BOTTOM" if self.pulse_shape else "TOP"
        self.rigol.write(f":SOUR1:BURS:IDLE {idle}") 
        self.rigol.write(":SYST:CSC CH1,CH2")
        
        # turn on output channels
        self.rigol.write(":OUTP1 ON")
        self.rigol.write(":OUTP2 ON")
        
        
       
        
        
        
        
        
        

 