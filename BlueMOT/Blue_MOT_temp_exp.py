# -*- coding: utf-8 -*-
"""
Created on Wed Jun  1 16:22:26 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 21:19:34 2022

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

import os
import h5py

from scipy.optimize import curve_fit
from numpy import unravel_index


import numpy as np
from scipy.optimize import least_squares
from scipy import constants


class Blue_MOT_temp(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=_Detection(self)
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[RangeScan(0.0*1e-3, 25.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
        
        self.setattr_argument("Detection_pulse_time",NumberValue(0.1*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
            
        if not hasattr(self.Delay_duration,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Delay_duration.sequence
        self.y=np.full(len(self.x), np.nan) # Prepare result array
        self.xdev = np.zeros(len(self.x)) # Prepare result array
        self.ydev = np.zeros(len(self.x)) # Prepare result array
      
    def prepare(self):  
       
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
       
        # Initialize camera
        self.Detect.camera_init()
      
    @kernel    
    def run(self):
        
        # general inicialization
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        
        delay(100*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
        self.BB.Probe_AOM_off()
        self.BR.Hp688_aom_off()
        delay(1*ms)

       
        # Main loop
        for ii in range(len(self.x)):
            self.Detect.arm()
            delay(800*ms)

            self.BB.MOT2D_off()  # turn off 2D MOT beam
            delay(1*ms)
            self.BB.Zeeman_off()
            delay(1*ms)

            # BACKGROUND IMAGE SEQUENCE
            if self.Background_subtract:
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for imaging
                delay(10*ms)
                self.BR.repumpers_on() # turn on repumpers
                self.Detect.trigger_camera()    # Trigger camera
                self.BB.MOT_on() #turn on mot for background image
                delay(self.Detection_pulse_time)
                self.BB.MOT_off()
                delay(self.Detect.Exposure_Time)
                self.BR.repumpers_off() # turn off repumpers
                self.Detect.acquire()     # Acquire images
                delay(100*ms)
                self.Detect.transfer_background_image(ii)
                delay(300*ms)
            ############################

            #prepare for detection image
            self.Detect.arm()
            delay(300*ms)

            self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading
            delay(1*ms)

            delay(1*ms)
            self.BR.repumpers_on() # turn on repumpers
            delay(1*ms)
            self.MC.Blackman_ramp_up()
            delay(1*ms)
            self.BB.Zeeman_on()
            delay(1*ms)
            self.BB.MOT2D_on() # Turn on atom beam
            delay(1*ms)
            self.BB.MOT_on()
            
            delay(1*ms)
            self.MC.flat()
            
            with parallel:
                self.BB.Zeeman_off()
                self.BB.MOT2D_off() # turn off atom beam
                self.BB.MOT_off() #turn off 3D 
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect) # switch to detection frequency
                self.BR.repumpers_off() # turn off repumpers
            
            delay(self.x[ii])  # Delay
            
            # IMAGING SEQUENCE
            self.BR.repumpers_on() # turn on repumpers
            self.Detect.trigger_camera()  # Trigger 
            self.BB.MOT_on()
            delay(self.Detection_pulse_time)
            self.BB.MOT_off()
            delay(self.Detect.Exposure_Time)
            self.BR.repumpers_off() # turn off repumpers
            delay(1*ms)
            ###########################
            self.MC.Set_current(0.0)
            
            self.Detect.acquire()                                # Acquire images
            delay(100*ms)
            self.Detect.transfer_image_background_subtracted(ii)
            delay(100*ms)
            self.Detect.disarm() 
          
            self.mutate_dataset("time_delay",ii,self.x[ii])
            self.mutate_dataset("detection.index",ii,ii)
            

        delay(500*ms)   
        self.MC.Zero_current()  
        
    def analyze(self):
        """
        analyze function takes the images generated in the run() function and
        fits gaussians to them to find atom cloud expansion as a function of time.
        This data is then fit to a parabola and solved for the temperature in 
        both directions.
        """
        pix2um = 67.8
        image_num = len(self.x)  # number of steps in TOF measurement
        popts = np.zeros((image_num, 6))  # fit parameters

        
        # ravel arrays appropriately to perform 2D fit
        pixel_num_x  = 152
        pixel_num_y = 260
        x = np.arange(0, pixel_num_x, 1)
        y = np.arange(0, pixel_num_y, 1)
        X, Y = np.meshgrid(x, y)
        xdata = np.vstack((X.ravel(), Y.ravel()))
        
        
        for ii in range(image_num):
            currentImage = self.get_dataset(f"detection.images.background_subtracted_image{ii}")
            
            cx, cy = unravel_index(currentImage.argmax(), currentImage.shape)  # estimate center+height
            val_max = currentImage[cx, cy]  
            
            initial_guess = (val_max, cx, cy, 100, 100, 0)
            
            # analyze image and add on to list of fit parameters
            popt, pcov = curve_fit(_twoDGaussian, xdata, currentImage.ravel(), p0=initial_guess);
            popts[ii,:] = popt

        # 24 microns per pixel is rough estimate, need to do more precise measurement on red mot        
        self.set_dataset("x_centers", pix2um*popts[:,1], broadcast=True) # relative position in um
        self.set_dataset("y_centers", pix2um*popts[:,2], broadcast=True)
        self.set_dataset("x_devs", pix2um**2*popts[:,3], broadcast=True) # dev squared in um^2
        self.set_dataset("y_devs", pix2um**2*popts[:,4], broadcast=True) 
        
        popt1, pcov1 = curve_fit(quadratic, self.x, popts[:,3])  # fit a quadratic to the cloud expansion
        popt2, pcov2 = curve_fit(quadratic, self.x, popts[:,4])
        
        ax = popt1[0]*pix2um**2*1e-12 # quadratic term in m^2/s
        ay = popt2[0]*pix2um**2*1e-12
        
        kb = constants.value('Boltzmann constant')
        M  = constants.value('atomic mass constant')*87.9
        Tx = ax*M/kb*1e6 # temp in uK
        Ty = ay*M/kb*1e6 # temp in uK
        
        
        self.set_dataset("Temp (uK)", np.array([Tx, Ty]), broadcast=True)
        print(Tx, Ty)
        print('## DONE ##')
        
                                      
        
def fit2DGaussian(x, y, A, center_x, center_y, sigma_x_sq, sigma_y_sq, offset):
    return A*np.exp(-((x-center_x)**2/(2*sigma_x_sq) + (y-center_y)**2/(2*sigma_y_sq)))

def _twoDGaussian(M, *args):
    x, y = M
    return fit2DGaussian(x, y, *args)
    
def quadratic(x, a, b, c):
    return a*x**2+b*x+c