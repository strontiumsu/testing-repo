# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class MOT_driver(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
    
        # 3D MOT driver
        
        # MOTdriver duration
        self.setattr_argument("Pulse_duration",
            Scannable(default=[NoScan(60*1e-3), RangeScan(10*1e-3, 30*1e-3, 10, randomize=False)],scale=1e-3,
                      unit="ms"),"MOT_driver")
        
        
        self.setattr_argument("MOT_t_ramp",NumberValue(0.0,min=-4.0,max=4.00,scale=1e-3,
                      unit="ms"),"MOT_driver")
        
        
        self.setattr_argument("Current_amplitude",NumberValue(0.0,min=-4.0,max=20.00,
                      unit="A"),"MOT_driver")
       
        self.setattr_argument("Npoints",NumberValue(3,min=0,max=100.00),"MOT_driver")
         
    def prepare(self):  
        #Ensure odd number of points for driver ramps
        print(self.Npoints)
        self.npoints=self.Npoints
        if self.Npoints % 2 == 0:
            self.npoints += 1
        
        print(self.npoints)
        w=np.blackman(self.npoints+1)  
        # repeat middle element
        self.w1=np.insert(w,int((self.npoints)/2),w[int((self.npoints)/2)])
        self.A=self.Current_amplitude
        self.dt=self.MOT_t_ramp/self.npoints/2    
        self.t_flat=self.Pulse_duration.value-2*self.MOT_t_ramp
        print(self.t_flat)
        

           
         
                  
    @kernel
    def run(self):
            self.core.reset()
            self.dac_0.init()
            for nn in range(9000):
                
                delay(10*ms)
                with parallel:
                    
                    
                    
                    with sequential:
                        
                        for ii in range(int(self.npoints+1)):
                            if ii<self.npoints/2:
                               delay(self.dt)
                               self.dac_0.write_dac(0,self.A*self.w1[ii])
                               self.dac_0.load()
                               ii+=1
                            elif ii==(self.npoints+1)/2:
                                self.ttl5.off()
                                delay(self.t_flat)
                                self.ttl5.off()
                                ii+=1
                            else:
                               delay(self.dt)
                               self.dac_0.write_dac(0,self.A*self.w1[ii])
                               self.dac_0.load()
                               ii+=1
                    
                    with sequential:
                       delay(self.MOT_t_ramp)
                       self.ttl5.off()
                       delay(400*ms)
                       self.ttl5.off()
            
                          
            self.dac_0.write_dac(0,self.A*0)
            self.dac_0.load()        
              


            
            
    
            
            
        

         

                     