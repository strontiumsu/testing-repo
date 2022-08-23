# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 22:29:39 2022

@author: sr
"""

# importing libraries
import cv2
import numpy as np
  
# reading the image data from desired directory
img = cv2.imread("bm0ms.png")
cv2.imshow('Image',img)
  
# counting the number of pixels
number_of_white_pix = np.sum(img == 100)
number_of_black_pix = np.sum(img == 0)
  
print('Number of white pixels:', number_of_white_pix)
print('Number of black pixels:', number_of_black_pix)