# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 18:30:48 2024

@author: ejporter
"""



from artiq.experiment import delay, NumberValue, ms, kernel, EnvExperiment, TInt32, BooleanValue
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import medfilt
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt

   

class _Camera2(EnvExperiment):
    
    def build(self):
        self.setattr_device("core") 
        self.setattr_device("ttl4")         # Camera hardware trigger
        self.cam=self.get_device("camera") # Thorlabs camera
        
        
        # 
        self.setattr_argument("Exposure_Time",NumberValue(1.5*1e-3,min=0.5e-3,max=100*1e-3,scale=1e-3,
                      unit="ms"),"Detection")        
        self.setattr_argument("Hardware_Gain",NumberValue(250,min=0,max=350,scale=1
                      ),"Detection")
        
        self.setattr_argument("Median_Filter",BooleanValue(False),"Detection")
        self.setattr_argument("Gaussian_Filter",BooleanValue(False),"Detection")
                
        # size of the image in pixels
        self.xsize = 404
        self.ysize = 304
        
        self.current_image = np.zeros((self.xsize, self.ysize)) 
        self.background_image = np.zeros((self.xsize, self.ysize)) 
        
    def prep_datasets(self,x):
        pass
   
        
    def camera_init(self, cam_range=None):
        # set camera settings
        if self.get_is_armed(): self.disarm()
        self.cam.set_exposure(self.Exposure_Time)
        self.cam.set_gain(self.Hardware_Gain)
        self.cam.set_roi(1250,1425,400,300)
        # self.cam_range = (50,-40, 30,-10)
        if cam_range is None:
            self.cam_range = (0,self.xsize,0,self.ysize)
        else:
            self.cam_range = cam_range
        self.cam.get_all_images() ## clears buffer
        
        self.ind = 0 # counts images
 
                  
    def arm(self, N=1):   
        # arm the camera with an N image buffer
        if not self.get_is_armed():
            self.cam.arm(N)
            
    def disarm(self):
        self.cam.disarm()
        
    def acquire(self, N=1):
        # acquire N images
        for _ in range(N):
            self.cam.acquire()
        
    def get_is_armed(self):
        return self.cam.get_is_armed()
                
    
               
    @kernel
    def trigger_camera(self):
       self.ttl4.on()
       delay(1*ms)
       self.ttl4.off()  
       
        
    def process_image(self, bg_sub=True):
        
        self.acquire(N=1+int(bg_sub))
        
        x1, x2, y1, y2 = self.cam_range
        imgs = np.copy(self.cam.get_all_images())
        
        self.current_image=imgs[0][x1:x2, y1:y2] # acquire
        self.background_image = np.zeros((x2-x1, y2-y1))
        if bg_sub: self.background_image=imgs[1][x1:x2, y1:y2]
        
        
        self.set_dataset(f"detection.images.Raw_{self.ind}", np.copy(self.current_image), broadcast=False)
        self.set_dataset(f"detection.images.BG_{self.ind}", np.copy(self.background_image), broadcast=False)
        if bg_sub:           
            self.current_image = np.subtract(self.current_image,self.background_image,dtype=np.int16)
        if self.Median_Filter:
            self.current_image = medfilt(self.current_image, 3)
        if self.Gaussian_Filter:
            self.current_image = gaussian_filter(self.current_image, 3)
        
        self.set_dataset(f"detection.images.Processed_{self.ind}", self.current_image, broadcast=False)


        display_image = np.copy(self.current_image)
        display_image = np.where(display_image > 0, display_image, 0)
        self.set_dataset("detection.images.current_image", display_image, broadcast=True)
              
        self.ind += 1
  
        





        

            
                
                
    
        
       
        
        