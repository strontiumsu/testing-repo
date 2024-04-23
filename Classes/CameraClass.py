# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 12:41:16 2023

@author: E. Porter
"""

from artiq.experiment import delay, NumberValue, ms, kernel, EnvExperiment, TInt32, BooleanValue
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import medfilt
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt

   

class _Camera(EnvExperiment):
    
    def build(self):
        """
        Camera
        Class to handle control of the thor labs cameras
        
        parameters:
        exposure_time: exposure time for a single image
        hardware_gain: gain setting for images

        """
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
                
        self.xsize = 170
        self.ysize = 112
        self.current_image = np.zeros((self.xsize, self.ysize)) 
        self.background_image = np.zeros((self.xsize, self.ysize)) 
        
    def prep_datasets(self,x):
        self.set_dataset("detection.counts",x, broadcast=True)    
        
    def camera_init(self):
        # set camera settings
        if self.get_is_armed(): self.disarm()
        self.cam.set_exposure(self.Exposure_Time)
        self.cam.set_gain(self.Hardware_Gain)
        #self.cam.set_roi(1150,1075,100,150) ###USED for 3-photon 689
        self.cam.set_roi(1250,1425,400,300)
        self.cam_range = (50,-40, 30,-10)

        # for data analysis
        self.pix2um = 67.8
        X, Y = np.meshgrid(np.arange(0, self.ysize, 1), np.arange(0, self.xsize, 1))
        self.xdata = np.vstack((X.ravel(), Y.ravel()))
        
        self.ind = 0

        #mot ranges horizontal push
        self.y1 = 70
        self.y2 = 200

        self.x1 = 100
        self.x2 = 270
        #self.x3 = 200
        
        # # mot ranges vertical push
        # self.y1 = 17
        # self.y2 = 60
        # self.y3 = 145

        # self.x1 = 165
        # self.x2 = 195
 
                  
    def arm(self):   
        # arm the camera
        if not self.get_is_armed():
            self.cam.arm(2)
        
    def acquire(self, N=1):
        # acquire N images
        for _ in range(N):
            self.cam.acquire()
        
    def get_is_armed(self):
        return self.cam.get_is_armed()
              
                
    def disarm(self):
        self.cam.disarm()
               
    def dispose(self):  
       self.cam.dispose()
    
    @kernel
    def trigger_camera(self):
       self.ttl4.on()
       delay(1*ms)
       self.ttl4.off()  
       
    @kernel
    def camera_delay(self, time):
        # add in a kernel function for delaying camera exposure
        delay(time)
        
    def process_image(self, save=True, name='', bg_sub=False):
        # pulls the current image, saves/bg subs as needed. Saves to current image dataset
        self.acquire()
        x1, x2, y1, y2 = self.cam_range
        self.current_image=np.copy(self.cam.get_all_images()[0])[x1:x2,y1:y2] # acquire and crop image
        if save:
            self.set_dataset(f"detection.images.Raw_{name}{self.ind}", self.current_image, broadcast=False)
        
        if bg_sub: 
            self.current_image = np.subtract(self.current_image,self.background_image,dtype=np.int16)
        if self.Median_Filter:
            self.current_image = medfilt(self.current_image, 3)
        if self.Gaussian_Filter:
            self.current_image = gaussian_filter(self.current_image, 3)
        if save:
            self.set_dataset(f"detection.images.{name}{self.ind}", self.current_image, broadcast=False)
        
        # Ranges for horizontal push
        #self.set_dataset(f"detection.images.ratio", int(10**6*((np.sum(self.current_image[self.x2:self.x3,self.y1:self.y2]))/(np.sum(self.current_image[self.x1:self.x3, self.y1:self.y2])))), broadcast=False)
        #self.set_dataset(f"detection.images.counts", int((np.sum(self.current_image[self.x2:self.x3,self.y1:self.y2]))), broadcast=True)
        
        #Ranges for vertical push
        #self.set_dataset(f"detection.images.ratio", int(10**6*((np.sum(self.current_image[self.x1:self.x2,self.y1:self.y2]))/(np.sum(self.current_image[self.x1:self.x2, self.y1:self.y3])))), broadcast=False)
        
        #self.set_dataset(f"detection.images.counts", int((np.sum(self.current_image[self.x1:self.x2,self.y1:self.y2]))), broadcast=True)
        self.set_dataset(f"detection.images.counts",int((np.sum(self.current_image[self.x1:self.x2,self.y1:self.y2]))/87), broadcast=True)
        self.set_dataset("detection.images.total_counts",int(np.sum(self.current_image)), broadcast=True)
        self.ind += 1
        
        
        # new camera code here:
        # pix_noise = np.average(self.current_image[120:143, 8:44])
        # red_counts = np.sum(self.current_image[self.x2:self.x3,self.y1:self.y2])- pix_noise*(self.x3-self.x2)*(self.y2-self.y1)
        # total_counts = np.sum(self.current_image[self.x1:self.x3, self.y1:self.y2])- pix_noise*(self.x3-self.x1)*(self.y2-self.y1)
        # prob = red_counts/total_counts
        
        # self.set_dataset("detection.images.ratio", int(10**6*(prob)), broadcast=False)
        # self.set_dataset("detection.images.counts", int(red_counts), broadcast=True)
        # self.ind += 1

        
        
        display_image = np.copy(self.current_image)
        
        # Display for rMOT
        display_image[self.x1:self.x2,   self.y2] = 200
        display_image[self.x1,   self.y1:self.y2+1] = 200
        display_image[self.x2,   self.y1:self.y2+1] = 200
        display_image[self.x2,   self.y1:self.y2+1] = 200
        
        #display for Bragg
        # display_image[  80:85, 140:145] = 50
        # display_image[  80:85, 165:170] = 50
        # display_image[  80:85, 190:195 ] = 50
        
        # Display for horizontal push
        # display_image[self.x1:self.x3+1,   self.y2] = 200
        # display_image[self.x1,   self.y1:self.y2+1] = 200
        # display_image[self.x2,   self.y1:self.y2+1] = 200
        # display_image[self.x3,   self.y1:self.y2+1] = 200
        # display_image[self.x2:self.x3+1,  self.y1] = 200
        # display_image[self.x2:self.x3+1,   self.y2] = 200
        # display_image[self.x2,   self.y1:self.y2+1] = 200
        # display_image[self.x3,   self.y1:self.y2+1] = 200
        
        # #Display for veritcal push
        # display_image[self.x1:self.x2+1,  self.y1] = 200
        # display_image[self.x1:self.x2+1,   self.y2] = 200
        # display_image[self.x1:self.x2+1,   self.y3] = 200
        # display_image[self.x1,   self.y1:self.y3+1] = 200
        # display_image[self.x2,   self.y1:self.y3+1] = 200
        
        

        display_image = np.where(display_image > 0, display_image, 0)
        self.set_dataset("detection.images.current_image", display_image, broadcast=True)
        
        #self.set_dataset("detection.images.MOT_range", [self.x1, self.x2, self.x3, self.y1, self.y2], broadcast=False)
        #self.set_dataset("detection.images.MOT_range", [self.x1, self.x2, self.x3, self.y1, self.y2], broadcast=False)
        
        self.disarm()
        
    def process_background(self):
        # processes the image from the background imaging
        self.acquire()
        x1, x3, y1, y2 = self.cam_range
        self.background_image = np.copy(self.cam.get_all_images()[0])[x1:x3,y1:y2]
        self.set_dataset("detection.images.background_image", self.background_image, broadcast=False)
        self.set_dataset("detection.images.current_image", self.background_image, broadcast=True)
        self.disarm()
    
    @kernel    
    def take_background(self):
        # takes background to subtract if wanted
        self.trigger_camera()
        self.camera_delay(self.Exposure_Time)
        delay(200*ms)
        self.process_background()

    @kernel
    def take_picture(self, save=True, name='', bg_sub=False):
        # triggers the camera and hands off to image processing
        self.trigger_camera()
        self.camera_delay(self.Exposure_Time)  
        self.process_image(save, name, bg_sub)
     
    def process_gaussian(self, index) -> TInt32:
        img = np.array(self.get_dataset("detection.images.current_image"))
        center_x, center_y = np.unravel_index(img.argmax(), img.shape)
        val_max = self.current_image[center_x, center_y]
        guess = [val_max, center_x, center_y, 30, 30, 0]
        popt, pcov = curve_fit(_twoDGaussian, self.xdata, img.ravel(), p0=guess, maxfev=15000)

              
                                                    
        return int(10**6*popt[index])
    
    def get_push_stats(self) -> TInt32:
        return self.get_dataset('detection.images.ratio')
    def get_push_stats_temp(self) -> TInt32:
        return int(10**6*self.get_dataset('detection.images.counts'))
    
    def get_count_stats(self,i) -> TInt32:
        self.mutate_dataset("detection.counts", i, self.get_dataset('detection.images.counts'))
        return self.get_dataset('detection.images.counts')
    
    def get_totalcount_stats(self) -> TInt32:
        return self.get_dataset('detection.images.total_counts')
    
    def get_peak(self) -> TInt32:
        img = np.array(self.get_dataset("detection.images.current_image"))
        cx, cy = np.unravel_index(img.argmax(), img.shape  )
        return int(cy)

        
def fit2DGaussian(x, y, A, center_x, center_y, sigma_x_sq, sigma_y_sq, offset):
    return A*np.exp(-((x-center_x)**2/(2*sigma_x_sq) + (y-center_y)**2/(2*sigma_y_sq)))

def _twoDGaussian(M, *args):
    x, y = M
    return fit2DGaussian(x, y, *args) 
        

            
                
                
    
        
       
        
        