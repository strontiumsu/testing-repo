# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 12:17:03 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np

   

class _Detection(EnvExperiment):
    def build(self):
        self.setattr_device("core") 
        self.setattr_device("ttl4")         # Camera hardware trigger
        self.cam=self.get_device("camera")  # Thorlabs camera
        self.setattr_argument("Exposure_Time",NumberValue(1.5*1e-3,min=1*1e-3,max=100*1e-3,scale=1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Hardware_gain",NumberValue(250,min=0,max=350,scale=1
                      ),"Detection")
        
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
        self.cam.acquire()
        
    def get_is_armed(self):
        return self.cam.get_is_armed()
    
    def camera_init(self):
          
           
           self.cam.set_exposure(self.Exposure_Time)
           self.cam.set_gain(self.Hardware_gain)
           self.cam.set_roi(1150,1075,100,150)
           # self.cam.frames_per_trigger_zero_for_unlimited = 0
 
    def prep_datasets(self,x):
            self.set_dataset("detection.index",x, broadcast=True)
            self.set_dataset("detection.image_sum", x, broadcast=True)
            self.set_dataset("detection.background_image_sum", x, broadcast=True)
            self.set_dataset("detection.background_subtracted_image_sum", x, broadcast=True)
            self.set_dataset("detection.deviationx", x, broadcast=True)
            self.set_dataset("detection.deviationy", x, broadcast=True)
            self.set_dataset("detection.Probup", x, broadcast=True)
            self.set_dataset("detection.rmot_sum", x, broadcast=True)
            
            # self.set_dataset("detection.image", x, broadcast=True)
            # self.set_dataset("detection.background_subtracted_image", x, broadcast=True)
        
     
    def transfer_background_image(self,i):
                self.background_image=np.copy(self.cam.get_all_images()[0])
                
                self.set_dataset("detection.images.background_image", self.background_image, broadcast=True)
                self.mutate_dataset("detection.background_image_sum",i,np.sum(self.background_image))
                self.cam.disarm()
                
    
    
    def transfer_image(self,i):
                image_buffer_copy1 = np.copy(self.cam.get_all_images()[0])

                self.mutate_dataset("detection.image_sum", i, np.sum(image_buffer_copy1))
                self.set_dataset("detection.images.image", image_buffer_copy1, broadcast=True)
                self.cam.disarm()
                
    def transfer_image_background_subtracted(self,i):
                self.image_buffer_copy1=np.copy(self.cam.get_all_images()[0])
                self.background_free_image= np.subtract(self.image_buffer_copy1,self.background_image,dtype=np.int16)

                self.background_free_image_display=np.where(self.background_free_image<0, 0, self.background_free_image)
                self.mutate_dataset("detection.image_sum", i, np.sum(self.image_buffer_copy1))
                self.set_dataset("detection.images.image", self.image_buffer_copy1, broadcast=True)
                
                self.mutate_dataset("detection.background_subtracted_image_sum",i, np.sum(self.background_free_image))
                self.set_dataset("detection.images.background_subtracted_image", self.background_free_image_display, broadcast=True)
                self.set_dataset(f"detection.images.background_subtracted_image{i}", self.background_free_image_display, broadcast=True)
                self.cam.disarm()     
        
    def calc_rmot_stats(self,i):
        
        x2 = 120-30
        x3 = 150+30
        y1 = 45-30
        y2 = 75+30
        
        noise = np.mean(self.background_free_image[x3+20:x3+70,y1:y2])
        
        numrmot = np.sum(self.background_free_image[x2:x3,y1:y2])-(x3-x2)*(y2-y1)*noise
        
        if numrmot <= 0:
            numrmot = 1
        
        #print(["1S0 data:",noise,(x2-x1)*(y2-y1)*noise,np.sum(self.background_free_image[x1:x2,y1:y2]),num1S0])
        #print(["3P1 data:",noise,(x3-x2)*(y2-y1)*noise,np.sum(self.background_free_image[x2:x3,y1:y2]),num3P1])
        

        self.background_free_image_display[x2:x3,y1]=200
        self.background_free_image_display[x2:x3,y2]=200
        self.background_free_image_display[x2,y1:y2]=200
        self.background_free_image_display[x3,y1:y2]=200

        self.set_dataset("detection.images.background_subtracted_image", self.background_free_image_display, broadcast=True)
        self.mutate_dataset("detection.rmot_sum", i, numrmot)

   
    def calc_push_stats(self,i):
        
        x1 = 79
        x2 = 135
        x3 = 165
        y1 = 45
        y2 = 95
        
        noise = np.mean(self.background_free_image[x3+20:x3+70,y1:y2])
        #print(noise)
        
        num1S0 = np.sum(self.background_free_image[x1:x2,y1:y2])#-(x2-x1)*(y2-y1)*noise
        num3P1 = np.sum(self.background_free_image[x2:x3,y1:y2])#-(x3-x2)*(y2-y1)*noise
        
        if num1S0 <= 0:
            num1S0 = 1
        if num3P1 <= 0:
            num3P1 = 1
        
        #print(["1S0 data:",noise,(x2-x1)*(y2-y1)*noise,np.sum(self.background_free_image[x1:x2,y1:y2]),num1S0])
        #print(["3P1 data:",noise,(x3-x2)*(y2-y1)*noise,np.sum(self.background_free_image[x2:x3,y1:y2]),num3P1])
        

        self.background_free_image_display[x2:x3,y1]=300
        self.background_free_image_display[x2:x3,y2]=300
        self.background_free_image_display[x2,y1:y2]=300
        self.background_free_image_display[x3,y1:y2]=300
        
        self.background_free_image_display[x1:x2,y1]=300
        self.background_free_image_display[x1:x2,y2]=300
        self.background_free_image_display[x1,y1:y2]=300
        self.background_free_image_display[x2,y1:y2]=300
        
        # if i == 0:
        #     self.set_dataset("detection.maxContrast",num3P1/(num3P1+num1S0),broadcast=True)

        self.set_dataset("detection.images.background_subtracted_image", self.background_free_image_display, broadcast=True)
        self.mutate_dataset("detection.Probup", i, num3P1/(num3P1+num1S0))
        #self.mutate_dataset("detection.Probup", i,( num3P1/(num3P1+num1S0) - 0.0441786826544748)/ 0.873846684266737)
        
        #print(len(np.transpose(self.background_free_image)[1]))
        #print(self.background_free_image[50:60,50:60]) 
        
                
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
        
        
    def dispose(self):  
       self.cam.dispose()
        
       
        
        