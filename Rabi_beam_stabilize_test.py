# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 17:38:38 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 16:08:51 2022

@author: sr
"""


from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from ZotinoRampClass import *
from Beamline461Class import*
from Beamline689Class import*
from HCDL import* 
from ThreePhoton689Class import* 

class Rabi_beam_stabilize_test(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("ttl6")
        self.setattr_device("ttl7")
        self.th_ph=ThreePhoton689(self)
        
        self.setattr_device("core_dma")
        self.setattr_device("zotino0") 
        self.dac=self.get_device("zotino0")

        self.setattr_argument("Rabi_t_pulse",
            Scannable(default=[RangeScan(0.0*1e-6, 5.0*1e-6, 20, randomize=False),NoScan(0.0)],scale=1e-6,
                      unit="us"),"Floppin")
        
        self.setattr_argument("Rabi_pulse_freq",
            Scannable(default=[RangeScan(60.0*1e+6, 80.0*1e+6, 20, randomize=False),NoScan(85.0*1e6)],scale=1e+6,
                      unit="MHz"),"Floppin")
        
        
        self.setattr_argument("Beam1_on",BooleanValue(False),"Floppin")
        self.setattr_argument("Beam2_on",BooleanValue(False),"Floppin")
        self.setattr_argument("Beam3_on",BooleanValue(True),"Floppin")
        
        self.setattr_argument("sw3_set", NumberValue(0.4,min=0.0,max=1.3),"Floppin")
        
        
        self.tscan=False
        self.x=[]
        
        if (not hasattr(self.Rabi_t_pulse,'sequence') and hasattr(self.Rabi_pulse_freq,'sequence')):
            self.t0=self.Rabi_t_pulse.value
            self.x=self.Rabi_pulse_freq.sequence
            self.f0=self.x[0]
            print(self.f0)
            self.tscan=False
            
        elif (hasattr(self.Rabi_t_pulse,'sequence') and not hasattr(self.Rabi_pulse_freq,'sequence')):
            self.f0=self.Rabi_pulse_freq.value
            self.x=self.Rabi_t_pulse.sequence
            self.t0=self.x[0]
            print(self.f0)
            self.tscan=True
            
        else:
           print('PICK ONE VARIABLE TO SCAN!')
         
        print(self.tscan)   
        self.y=np.full(len(self.x), np.nan) # Prepare result array
        
    def prepare(self):  
        
        
        self.th_ph.set_atten()        
        self.sw3_setpt = self.sw3_set*(1.0)
    
        
   
    @kernel    
    def run(self):
        
        # general inicialization
        self.core.reset()
        self.th_ph.init_aoms()
        self.ttl7.off()
        self.dac.init()
        delay(10*ms)
        delay(100*ms)
        self.dac.write_dac(7,self.sw3_setpt)
        self.dac.load()

       
        self.th_ph.switch1_off()
        delay(1*ms)
        self.th_ph.switch2_off()
        delay(1*ms)
        self.th_ph.switch3_off()
       
        # Main loop
        for ii in range(len(self.x)):
   
            
            delay(100*ms)    

            with sequential:
                delay(500*us)
                with parallel:
                    self.th_ph.switch2_on()
                    with sequential:
                        delay(0.65*us)
                        self.th_ph.switch3_on()
                    with sequential:
                        delay(0.5*us)
                        self.th_ph.switch1_on()

                delay(self.x[ii])
                
                with parallel:
                    self.th_ph.switch2_off()
                    with sequential:
                        delay(0.65*us)
                        self.th_ph.switch3_off()
                    with sequential:
                        delay(0.5*us)
                        self.th_ph.switch1_off()

            delay(100*ms)
        
    