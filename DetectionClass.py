# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 17:57:45 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 12:17:03 2021

@author: sr
"""
from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   

class DetectionNew(EnvExperiment):
    def build(self):

        self.setattr_device("core") 
        self.setattr_device("ttl4")         # Camera hardware trigger
        self.cam=self.get_device("camera")  # Thorlabs camera
        # self.available_cameras = TLCameraSDK().discover_available_cameras()
        # if len(self.available_cameras) < 1:
        #     print("no cameras detected")

        # self.cam = TLCameraSDK().open_camera(self.available_cameras[0])
        
        self.setattr_argument("Exposure_Time",NumberValue(25*1e-3,min=1*1e-3,max=100*1e-3,scale=1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Hardware_gain",NumberValue(100,min=1,max=1000,scale=1
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
        self.cam.arm(2)
        
    def acquire(self):
        #self.cam.acquire()
            frame = self.cam.get_pending_frame_or_null()
            if frame is not None:
                print("frame #{} received!")

                frame.image_buffer  # .../ perform operations using the data from image_buffer

                #  NOTE: frame.image_buffer is a temporary memory buffer that may be overwritten during the next call
                #        to get_pending_frame_or_null. The following line makes a deep copy of the image data:
                image_buffer_copy = np.copy(frame.image_buffer)
                print(image_buffer_copy)
            else:
                print("timeout reached during polling, program exiting...")
        
    
    def camera_init(self):
        
        self.cam.exposure_time_us = 11000  # set exposure to 11 ms
        self.cam.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
        self.cam.image_poll_timeout_ms = 1000  # 1 second polling timeout
        #old_roi = camera.roi  # store the current roi
        """
        uncomment the line below to set a region of interest (ROI) on the camera
        """
        self.cam.roi = (1000,900,500,500)  # set roi to be at origin point (100, 100) with a width & height of 500

        """
        uncomment the lines below to set the gain of the camera and read it back in decibels
        """
        # if self.cam.gain_range.max > 0:
        #     db_gain = 6.0
        #     gain_index = self.cam.convert_decibels_to_gain(db_gain)
        #     self.cam.gain = gain_index
        #     print(f"Set camera gain to {camera.convert_gain_to_decibels(camera.gain)}")
            
           # self.cam.disarm() 
           # self.cam.set_exposure(self.Exposure_Time)
           # self.cam.set_gain(self.Hardware_gain)
           # self.cam.set_roi(1000,900,500,500)
           #self.cam.frames_per_trigger_zero_for_unlimited = 0
 
    def prep_datasets(self,x):
            self.set_dataset("detection.index",x, broadcast=True)
            self.set_dataset("detection.image_sum", x, broadcast=True)
            self.set_dataset("detection.background_image_sum", x, broadcast=True)
            self.set_dataset("detection.background_subtracted_image_sum", x, broadcast=True)
     
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
        
        
        