# # -*- coding: utf-8 -*-
# """
# Created on Tue Jun  4 10:56:31 2024

# @author: E. Porter
# """

from artiq.experiment import *

# imports
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

class NICEOHMS_exp(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        
        self.setattr_device("sampler0")
        self.adc_0=self.get_device("sampler0") 
        
        self.setattr_argument("sample_rate", NumberValue(1.0*1e3,min=0.0*1e3,max=20.0*1e3,scale=1e3,
                      unit="kHz"),"Params")
        self.setattr_argument("sampling_time", NumberValue(5.0*1e0,min=0.1*1e0,max=20.0*1e0,scale=1e0,
                      unit="s"),"Params")
        
        self.setattr_argument("start_freq", NumberValue(991.5*1e6,min=0.0*1e6,max=1500.0*1e6,scale=1e6,
                      unit="MHz"),"Params")
        self.setattr_argument("stop_freq", NumberValue(993.5*1e6,min=0.0*1e6,max=1500.0*1e6,scale=1e6,
                      unit="MHz"),"Params")
        self.setattr_argument("V_delta", NumberValue(10.35,min=0.0,max=11,scale=1,
                      unit="V"),"Params")
        self.setattr_argument("Plot", BooleanValue(True),"Params")

        
    def prepare(self):
        self.saving = False        
        self.NUM_CHANNELS = 8      
        self.last_val = -1.0
        self.num_samples = int(self.sampling_time * self.sample_rate)
        self.data = [[0.0] * self.NUM_CHANNELS for _ in range(self.num_samples)]
        ## data channels: chan1 = ramp voltage, chan0 = PD reading 
    
    @kernel
    def run(self):
        
        
        self.core.reset()
        self.adc_0.init()
        self.core.break_realtime()  
 
        i = 0
        while i < self.num_samples:
            # print(i)
            # self.core.break_realtime()
            at_mu(now_mu())
            if not self.saving:
                self.adc_0.sample(self.data[0])
                
                if self.data[0][1] + 0.5 < self.last_val:
                    self.saving = True
                else:
                    self.last_val = self.data[0][1]
                delay_mu(int(self.core.seconds_to_mu(1 / self.sample_rate)))
            else:                
                self.adc_0.sample(self.data[i])  
                i += 1
                delay(1*ms)
            
   
        self.process_data(self.data)
        
    @rpc(flags={"async"})
    def process_data(self, data):
        # This function runs outside the kernel and can be used for post-processing
        self.post_process(data)
    def moving_average(self, x, w):
        return np.convolve(x, np.ones(w), 'valid') / w
    
    def post_process(self, data):

        def gaussian(x, a, x0, sigma, y0):
            return a * np.exp(-(x - x0)**2 / (2 * sigma**2)) + y0
        
        def lor(x, a, x0, g, y0):
            return a * (g/2)/((x-x0)**2+(g/2)**2)+y0
        
        data = np.array(data[:int(len(data)*0.98)]) # turns into numpy array and cuts off last tiny bit of data to keep clean
        
        trans = data[:,0]
        #trans = self.moving_average(trans, 20)
        
        
        x = data[:,1]
        v = self.start_freq + x/self.V_delta*(self.stop_freq-self.start_freq)
        v = v/1e6
        # v = v[19:]
        
        initial_guess = [max(trans), v[np.argmax(trans)], 1, 0]
        print(initial_guess)
        
        try:
            #popt, pcov = curve_fit(gaussian, v, trans, p0=initial_guess, maxfev=20000)
            #a, v0, sigma, y0 = popt
            
            popt, pcov = curve_fit(lor, v, trans, p0=initial_guess, maxfev=20000)
            a, v0, sigma, y0 = popt
            
            print(np.round(1000*np.sqrt(pcov[1][1]),3))
            print(np.round(v0, 4))
        except RuntimeError as e:
            print(f"Error fitting Gaussian: {e}")
        
        if self.Plot:
            plt.scatter(v, trans, s=0.2)
            #plt.plot(v, gaussian(v, *popt), color='orange')  
            plt.plot(v, lor(v, *popt), color='orange')  
            plt.xlabel("Frequency (MHz)")
            plt.ylabel("Transmission (V)")
            plt.title("Transmission vs. offset frequency")
            plt.show()
