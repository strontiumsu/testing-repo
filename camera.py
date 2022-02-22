# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 12:17:03 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   

 

class Detection(EnvExperiment):
    def build(self):

        self.setattr_device("ttl4")         # Camera hardware trigger
        self.cam=self.get_device("camera")  # Thorlabs camera
        
        self.setattr_argument("Exposure_Time",NumberValue(25*1e-3,min=10*1e-3,max=100*1e-3,scale=1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Reps",NumberValue(5,min=1,max=100, ndecimals = 0, scale = 1,step=1,type='int'),"Detection")
        
   

        self.y=np.empty(self.Reps)      # 
        self.x=np.empty(self.Reps)
        
        
    @kernel
    def trigger_camera(self):
       delay(750*ms)
       self.ttl4.on()
       delay(1*ms)
       self.ttl4.off()  
       
    @kernel
    def kernel_delay(self,t):
        delay(t)        
        
    def camera_init(self):
           self.cam.disarm() 
           self.cam.set_exposure(self.Exposure_Time)
           self.cam.set_roi(1370,450,300,200)
 
    def data_sets(self):
            self.set_dataset("index",self.x, broadcast=True,persist=True)
            self.set_dataset("image_mean", self.y, broadcast=True,persist=True)
     
            

  
            
             
           
            for i in range(len(self.y)):
                #delay(5*ms)
                self.cam.arm(2)


                
                self.trigger_cam()
                
                ##delay(2*ms)
                self.cam.acquire()
                #delay(100*ms)
                #if v<2.0:
                
                self.kernel_delay(1) 
                
                #delay(100*ms)
                
                
                
                # v=v+0.05
                #else:
                image_buffer_copy1 = self.cam.get_all_images()[0]
                self.y[i]=np.mean(image_buffer_copy1)
                self.mutate_dataset("index",i, i)
                self.mutate_dataset("image_mean", i,self.y[i])
                self.set_dataset("image", image_buffer_copy1, broadcast=True)
                
                self.cam.disarm()
            #self.dac_0.write_dac(0,0.0)
            #self.dac_0.load()
            
            
                
                
    def analyze(self): 
        
        
            #ims=self.cam.get_all_images()
            self.cam.disarm()
        
            #exp = ims
            
            #self.set_dataset("images", exp, broadcast=True)
            #self.cam.disconnect()

            #for ii in range(len(ims)):