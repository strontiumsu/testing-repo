# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 13:26:48 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np 

from scipy.optimize import curve_fit   
import os
import h5py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
   
from DetectionClass import _Detection
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689
from ThreePhoton689Class import _ThreePhoton689 

class Rabi_flopping_v2(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("ttl6")
        self.setattr_device("ttl7")
        self.setattr_device("ttl0")
        self.setattr_device("scheduler")
        self.Detect=_Detection(self)
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        self.th_ph=_ThreePhoton689(self)
        
        
    
        #self.Zot = ZotinoRamp(self)
        
        # MOTdriver parameters
        self.setattr_argument("Red_pulse_duration",NumberValue(200.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Bottom_current_amplitude",NumberValue(0.0,min=0.0,max=5.00,
                      unit="A"),"MOT coil driver")
        
        self.setattr_argument("Bottom_delay",NumberValue(0.0,min=0.0,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Red_current_amplitude",NumberValue(0.0,min=0.0,max=9.00,
                      unit="A"),"MOT coil driver")
       
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Push_pulse_time",NumberValue(1.0*1e-6,min=0.0*1e-6,max=500.00*1e-3,scale = 1e-9,
                      unit="ns"),"Detection")
        
        self.setattr_argument("Delay_duration",
            NumberValue(5,min=0.0*1e-6,max=15000.00*1e-6,scale = 1e-6,
                      unit="us"),"Detection")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
            
        
        self.setattr_argument("Rabi_t_pulse",
            Scannable(default=[RangeScan(0.0*1e-6, 5.0*1e-6, 20, randomize=False),NoScan(0.0)],scale=1e-6,
                      unit="us"),"Floppin")
        
        self.setattr_argument("Rabi_pulse_freq",
            Scannable(default=[RangeScan(60.0*1e+6, 80.0*1e+6, 20, randomize=False),NoScan(85.0*1e6)],scale=1e+6,
                      unit="MHz"),"Floppin")
        
        self.setattr_argument("Plot",BooleanValue(False),"Plotting")
        
        
        self.setattr_argument("Beam1_on",BooleanValue(False),"Floppin")
        self.setattr_argument("Beam2_on",BooleanValue(False),"Floppin")
        self.setattr_argument("Beam3_on",BooleanValue(True),"Floppin")
        
        
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
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        #self.Zot.Linear_ramp_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
        self.th_ph.set_atten()
        # Initialize camera
        self.Detect.camera_init()
        #self.Detect.disarm()

        
    @kernel    
    def run(self):
        
        # general inicialization
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        self.th_ph.init_aoms()
        
        self.ttl0.output()
        delay(1*ms)
        self.ttl0.off()

        Lin_ramp_time = 100*ms
        
        self.ttl7.off()
        

        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        delay(10*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
        self.BB.Probe_AOM_off()
        delay(1*ms)
        self.BR.Hp688_aom_off()
        delay(1*ms)
        self.th_ph.switch1_off()
        delay(1*ms)
        self.th_ph.switch2_off()
        delay(1*ms)
        self.th_ph.switch3_off()
       
        # Main loop
        for ii in range(len(self.x)):
            self.Detect.arm()
            
            delay(175*ms)

            self.BB.MOT2D_off()  # turn off 2D MOT beam
            delay(1*ms)
            self.BB.Zeeman_off()
            delay(1*ms)
            
            # Set 689 AOM detuning
            if not self.tscan:
                if self.Beam1_on:
                    self.th_ph.set_switch1_689_3nu_freq(self.x[ii])
                if self.Beam2_on:
                    self.th_ph.set_switch2_689_3nu_freq(self.x[ii])
                if self.Beam3_on:
                    self.th_ph.set_switch3_689_3nu_freq(self.x[ii])
                   
            else:
              
                if self.Beam1_on:
                    self.th_ph.set_switch1_689_3nu_freq(self.f0)
                if self.Beam2_on:
                    self.th_ph.set_switch2_689_3nu_freq(self.f0)
                if self.Beam3_on:
                    self.th_ph.set_switch3_689_3nu_freq(self.f0)
            
            
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
                delay(50*ms)
                self.Detect.transfer_background_image(ii)
                delay(50*ms)
            ############################

            #prepare for detection image
            self.Detect.arm()
            delay(175*ms)

            self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading
            delay(10*ms)
            
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
                self.MC.Set_current(self.Bottom_current_amplitude) #ramp down Blue mot coils  
                self.ttl5.off()

            delay(self.Bottom_delay)
            self.BR.repumpers_off() # turn off repumpers
            self.MC.Linear_ramp(self.Bottom_current_amplitude,self.Red_current_amplitude,Lin_ramp_time,30)

            with parallel:
                self.ttl5.on() #turn off modulation channel
                self.ttl6.on() #switch to single-frequency channel
            delay(self.Red_pulse_duration) #single frequency stage time
            self.ttl6.off() #switch back to mod channel (which is off)

            self.MC.Set_current(0.0)
            #delay(500*us)
            self.ttl7.on() # trigger quantiation B field pulse
                
            
            with parallel:
                with sequential:
                    delay(698.75*us)
                    if self.tscan:
                        delay(self.x[ii])
                    else:
                        delay(self.t0)
                    with parallel:
                        self.BB.Probe_AOM_on()
                        self.BR.Hp688_aom_on()
                        #delay(1.25*us)
                        self.BR.repumpers_on() # turn on repumpers
                
                if self.Beam1_on:
                    with sequential:
                        delay(700*us)
                        self.th_ph.switch1_on()
                        self.ttl0.on()
                        if self.tscan:
                            delay(self.x[ii])
                        else:
                            delay(self.t0)
                        self.ttl0.off()    
                        self.th_ph.switch1_off()

                        
                if self.Beam2_on:
                    with sequential:
                        delay(700*us)
                        self.th_ph.switch2_on()
                        if self.tscan:
                            delay(self.x[ii])
                        else:
                            delay(self.t0)
                        self.th_ph.switch2_off()
                
                if self.Beam3_on:
                    with sequential:
                        delay(700*us)
                        self.th_ph.switch3_on()
                        if self.tscan:
                            delay(self.x[ii])
                        else:
                            delay(self.t0)
                        self.th_ph.switch3_off()

            delay(self.Push_pulse_time)
            
            with parallel:
                self.BR.repumpers_off() # turn off repumpers
                self.BB.Probe_AOM_off()
                self.BR.Hp688_aom_off()
            
            self.ttl7.off() #reset B field pulse trigger
            delay(self.Delay_duration)
            
            # IMAGING SEQUENCE
            self.BR.repumpers_on() # turn on repumpers
            self.Detect.trigger_camera()  # Trigger 
            self.BB.MOT_on()
            delay(self.Detection_pulse_time)
            self.BB.MOT_off()
            delay(self.Detect.Exposure_Time)
            self.BR.repumpers_off() # turn off repumpers
            ###########################

           
            
            self.Detect.acquire()                                # Acquire images
            delay(50*ms)
            self.Detect.transfer_image_background_subtracted(ii)
            delay(50*ms)
            #self.Detect.disarm() 
          
            self.mutate_dataset("time_delay",ii,self.x[ii])
            self.mutate_dataset("detection.index",ii,ii)
            
            
            self.Detect.calc_push_stats(ii)
           
           
        delay(500*ms)   
        self.MC.Zero_current()  
        
    def analyze(self):
        if not hasattr(self.Rabi_t_pulse,'sequence'):
            return None
        
        initial_guess = [1, 2, 0.4, 1,0] # [omega (MHz), omega_gen (MHz), s.s., tau]
        
        t = np.array(self.x)*1e6 # us
        y = np.array(self.get_dataset("detection.image_sum"))
        
        popt, pcov = curve_fit(RabiFunc, t, y, p0=initial_guess, maxfev = 50000);
        omega, omega_gen, ss, tau, dt = popt
        
        print("Generalized Rabi Frequency: " + str(np.round(omega_gen/(2*np.pi),2)) + " MHz. Cov = " + str(pcov[1][1]) )
        print("Decay Rate: " + str(np.round(tau,2)) + " us. Cov = " + str(pcov[3][3]))
        self.set_dataset("Gen Freq (MHz)", np.round(omega_gen/(2*np.pi),2), broadcast=True)
        self.set_dataset("Decay (us)", np.round(tau,2), broadcast=True)
        self.set_dataset("Gen Freq (MHz) [cov]", np.round(pcov[1][1],2), broadcast=True)
        self.set_dataset("Decay (us) [cov]", np.round(pcov[3][3],2), broadcast=True)
        
        if self.Plot:
            fig, ax = plt.subplots()
        
            ax.scatter(t, y)
            
            t = np.linspace(t[0], t[-1], 500)
            ax.plot(t, RabiFunc(t, *popt), color = 'red')
            
            ax.set_ylim(-0.1,1)
            ax.set_xlim(-0.2, t[-1]+0.2)
            
            
            ax.text(t[-1]*0.7, 0.85, f'$\Omega^\prime = 2\pi x ${np.round(omega_gen/(2*np.pi),2)} MHz')
            ax.text(t[-1]*0.7, 0.75, f'$tau$ ={np.round(tau,2)} us')
            
            ax.set_xlabel("Time (us)", fontsize=14)
            ax.set_ylabel("$P_e$", fontsize=14)
            
            ax.tick_params(axis="x", direction='in', width=2, length=6)
            ax.tick_params(axis="y", direction='in', width=2, length=6)
            
            
            #date = time.strftime("%y-%m-%d/%H/")
            RID = self.scheduler.rid
            #path = "C:/Users/sr/Documents/Artiq/artiq-master/results/" + date + str(RID) + "_plot.png"
            
            ax.set_title("RID: " + str(RID))
            
            plt.show()
            #plt.savefig(path)
        
        print(popt)
        print('## DONE ##')

        
        
def RabiFunc(t, omega, omega_gen, ss, tau,dt):
     return ss + np.e**(-(t-dt)/tau)*(omega**2/(2*omega_gen**2)*(1-np.cos(omega_gen*(t-dt)))-ss)   