#!/usr/bin/env python3
# software to convert raw centre of pressure (COP) data into various COP based measures of balance
# uses code and a module (hyperellipsoid.py) written by 'Marcos Duarte,
# https://github.com/demotu/BMC' for calculating area of a 95% prediction
# ellipse

# TO DO
# ask user to choose directory
# read all files matching a glob expression e.g. *.dat
# read in and unpickle the data


# IMPORTS
# ~~~~~~~
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
# %matplotlib inline
# next line assumes hyperellipsoid.py is in same directory
from hyperellipsoid import hyperellipsoid
from tkinter import *

# DEFINITIONS
# ~~~~~~~~~~~

# GET FILES TO READ
# ~~~~~~~~~~~~~~~~~

# GET USER TO CHOOSE COP PARAMETERS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cop_params = ['95% prediction interval', 'path length']
root = Tk()
root.title('Choose parameters to calculate')
lb = Listbox(root, selectmode=MULTIPLE)
for choice in cop_params:
    lb.insert(END, choice)
lb.pack()
#butt = Button(root, text='OK', command=select_all)
#butt.pack()
root.mainloop()

# test data
y = np.cumsum(np.random.randn(3000)) / 50
x = np.cumsum(np.random.randn(3000)) / 100
# calculate ellipsoid parameters
area, axes, angles, center, R = hyperellipsoid(x, y, units='cm', show=True)
