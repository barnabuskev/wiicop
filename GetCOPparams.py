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
import tkinter.filedialog as tk_fd
import sys
import os
import re
import pickle
import pandas
import matplotlib.pyplot as plt
# %matplotlib inline
# next line assumes hyperellipsoid.py is in same directory
from hyperellipsoid import hyperellipsoid


# INITIALISE
# set regular expression to find calibration file
cal_re = "calib.*dat"
# set regular expression to find cop data file
cop_re = "subj.*.dat"

# setup regular expressions
cal_re_o = re.compile(cal_re)
cop_re_o = re.compile(cop_re)

# SEARCH THROUGH CHOSEN DIRECTORY STRUCTURE
seshd = tk_fd.askdirectory(title = 'Open study directory containing sessions')
if not seshd:
    sys.exit()
tst = os.walk(seshd)
for root, dirs, files in os.walk(seshd):
    # for each directory level
    if len(files) > 0:
        # do stuff with files...
        # look for calibration file using reg expression
        c_lst = list(filter(cal_re_o.match,files))
        if c_lst:
            # if list c_lst is not empty..
            # should contain only one file name
            assert len(c_lst)==1
            # open calibration file
            c_pth = os.path.join(root,c_lst[0])
            with open(c_pth,'rb') as fptr:
                cal_dat = pickle.load(fptr, fix_imports=False)
            print(cal_dat['details'])
        # look for cop data file using reg expression
        d_lst = list(filter(cop_re_o.match,files))
        if d_lst:
            # if list d_lst is not empty..
            # print(d_lst)
            pass
    if len(dirs) > 0:
        # do stuff with directories?
        pass
