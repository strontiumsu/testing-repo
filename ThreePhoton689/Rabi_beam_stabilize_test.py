# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 17:38:38 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np  
   
from DetectionClass import _Detection
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689
from ThreePhoton689Class import _ThreePhoton689 

class Rabi_beam_stabilize_test(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl0")
        self.setattr_device("ttl5")
        self.setattr_device("ttl6")
        self.setattr_device("ttl7")
        self.th_ph=_ThreePhoton689(self)
        
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
            self.tscan=False
            
        elif (hasattr(self.Rabi_t_pulse,'sequence') and not hasattr(self.Rabi_pulse_freq,'sequence')):
            self.f0=self.Rabi_pulse_freq.value
            self.x=self.Rabi_t_pulse.sequence
            self.t0=self.x[0]
            self.tscan=True
            
        # else:
        #    print('PICK ONE VARIABLE TO SCAN!')
           
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
        self.ttl0.output()
        delay(1*ms)
        self.ttl0.off()
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
       
        delay(1*ms) 
        #self.th_ph.switch1_on()
        delay(1*ms)
        
        # Main loop
        for jj in range(1):
            for ii in range(len(self.x)):
                delay(1*ms) 
                
                delay(100*ms)
                # Set 689 AOM detuning
                if not self.tscan:
                   self.th_ph.set_switch1_689_3nu_freq(self.x[ii])
                #delay(100*ms)    
                #self.ttl7.on()
                
                
                with parallel:
                    
                    with sequential:
                        delay(200*us)
                        self.th_ph.switch1_on()
                        #delay(0.1*us)
                        self.ttl0.on()
                        if self.tscan:
                            delay(self.x[ii])
                        else:
                            delay(self.t0)
                        
                        
                        self.ttl0.off()    
                        #delay(1*us)
                        self.th_ph.switch1_off()
                        

                    with sequential:
                        delay(200*us)
                        self.th_ph.switch2_on()
                        if self.tscan:
                            delay(self.x[ii])
                        else:
                            delay(self.t0)
                        self.th_ph.switch2_off()
                    
                    with sequential:
                        delay(200*us)
                        self.th_ph.switch3_on()
                        if self.tscan:
                            delay(self.x[ii])
                        else:
                            delay(self.t0)
                        self.th_ph.switch3_off()
                        
                
                delay(10*us)
                
                #self.th_ph.switch1_off()
                        
                # with parallel:
                    
                #     with sequential:
                #         self.ttl0.on()
                #         self.th_ph.switch1_on()
                #         if self.tscan:
                #             delay(self.x[ii])
                #         else:
                #             delay(self.t0)
                #         self.th_ph.switch1_off()
                #         self.ttl0.off()

                #     with sequential:
                #         self.th_ph.switch2_on()
                #         if self.tscan:
                #             delay(self.x[ii])
                #         else:
                #             delay(self.t0)
                #         self.th_ph.switch2_off()
                    
                #     with sequential:
                #         self.th_ph.switch3_on()
                #         if self.tscan:
                #             delay(self.x[ii])
                #         else:
                #             delay(self.t0)
                #         self.th_ph.switch3_off()
                delay(200*ms)
                self.ttl7.off()
                self.ttl0.off()
                
        
    