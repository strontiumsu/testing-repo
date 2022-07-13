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

        self.setattr_device("core") 
        self.setattr_device("ttl4")         # Camera hardware trigger
        self.cam=self.get_device("camera")  # Thorlabs camera
        
        self.setattr_argument("Exposure_Time",NumberValue(25*1e-3,min=1*1e-3,max=100*1e-3,scale=1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Hardware_gain",NumberValue(100,min=0,max=350,scale=1
                      ),"Detection")
        
        #self.setattr_argument("N_reps",NumberValue(2000,min=1,max=2000, ndecimals = 0, scale = 1,step=1,type='int'),"Detection")
        

        
        
    @kernel
    def trigger_camera(self):
       self.ttl4.on()
       delay(1*ms)
       self.ttl4.off()  
       
       
       
    @kernel
    def kernel_delay(self,t):
        delay(t)        
        
    
    
    def arm(self):
        self.cam.arm(1)
        
    def acquire(self):
        self.cam.acquire()
        
    
    def camera_init(self):
           self.cam.disarm() 
           self.cam.set_exposure(self.Exposure_Time)
           self.cam.set_gain(self.Hardware_gain)
           self.cam.set_roi(1225,1050,200,200)
           #self.cam.frames_per_trigger_zero_for_unlimited = 0
 
    def prep_datasets(self,x):
            self.set_dataset("detection.index",x, broadcast=True)
            self.set_dataset("detection.image_sum", x, broadcast=True)
            self.set_dataset("detection.background_image_sum", x, broadcast=True)
            self.set_dataset("detection.background_subtracted_image_sum", x, broadcast=True)
            self.set_dataset("detection.deviationx", x, broadcast=True)
            self.set_dataset("detection.deviationy", x, broadcast=True)
        
     
    def transfer_background_image(self,i):
                self.background_image=np.copy(self.cam.get_all_images()[0])
                self.set_dataset("detection.background_image", self.background_image, broadcast=True)
                self.mutate_dataset("detection.background_image_sum",i,np.sum(self.background_image))
                self.cam.disarm()
                
    
    
    def transfer_image(self,i):
                image_buffer_copy1 = np.copy(self.cam.get_all_images()[0])
             
                #self.mutate_dataset("index",i, i)
                self.mutate_dataset("detection.image_sum", i, np.sum(image_buffer_copy1))
                self.set_dataset("detection.image", image_buffer_copy1, broadcast=True)
                
                self.cam.disarm()
                
    def transfer_image_background_subtracted(self,i):
                self.image_buffer_copy1=np.copy(self.cam.get_all_images()[0])
                self.background_free_image= np.subtract(self.image_buffer_copy1,self.background_image,dtype=np.int16)
                
                self.background_free_image=np.where(self.background_free_image<0, 0, self.background_free_image)
                self.mutate_dataset("detection.image_sum", i, np.sum(self.image_buffer_copy1))
                self.set_dataset("detection.image", self.image_buffer_copy1, broadcast=True)
                
                #self.mutate_dataset("index",i, i)
                
                self.mutate_dataset("detection.background_subtracted_image_sum",i, np.sum(self.background_free_image))
                self.set_dataset("detection.background_subtracted_image", self.background_free_image, broadcast=True)
                
                self.cam.disarm()     
  
                
    def calc_marginal_stats(self,i):
        tot = np.sum(self.background_free_image)
        
        #ly = 200
        
        ix = self.background_free_image/np.sum(self.background_free_image)
        iy = np.transpose(self.background_free_image)/np.sum(self.background_free_image)

        lx = 110
        ux = 170
        ly = 1
        uy = 190
        
        lenx = ux-lx
        leny = uy-ly
        
        datax = np.zeros(lenx)
        datay = np.zeros(leny)
        
        for j in range(lenx):
            datax[j] = np.sum(ix[j+lx])
        for j in range(leny):
            datay[j] = np.sum(iy[j+ly])
            
        datax = datax/np.sum(datax)
        datay = datay/np.sum(datay)

        # for j in range(len(ix[0])):
        #     datax[j] = np.sum(ix[j])
        # for j in range(ly):
        #     datay[j] = np.sum(iy[j])
            
        meanx = 0.
        meany = 0.

        for j in range(lenx):
            meanx = meanx + j*datax[j]
        for j in range(leny):
            meany = meany + j*datay[j]
    
        varx = 0.
        vary = 0.
        for j in range(lenx):
            varx = varx + ((j-meanx)**2)*datax[j]
        for j in range(leny):
            vary = vary + ((j-meany)**2)*datay[j]
               
        self.mutate_dataset("detection.deviationx", i, np.sqrt(varx))
        self.mutate_dataset("detection.deviationy", i, np.sqrt(vary))
        
        self.set_dataset("detection.margx", datax, broadcast=True)
        self.set_dataset("detection.margy", datay, broadcast=True)
                
    def return_bg_subtracted_image_array(self):     
        return self.background_free_image
                
    def print_image_array(self):
               print('Image array: ')
               print(self.image_buffer_copy1)      
    def print_bg_image_array(self):
               print('Background image array: ')
               print(self.background_image)           
   
    def print_bg_subtracted_image_array(self):
               print('Background subtracted image array: ')
               print(self.background_free_image)     
            
            
                
                
    def disarm(self):
        self.cam.disarm()
        #self.cam.dispose()
        
        
        