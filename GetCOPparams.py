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
import pandas as pd
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

# create empty pandas dataframes to store calibration and cop data
cal_df=pd.DataFrame(columns=['session','sensor','slope','slope.se','r.coef','p-val'])
# NEED TO READ IN CONFIG FILE BEFORE DOING THIS ***
cop_df=pd.DataFrame(columns=['study','sensor','slope','slope.se','r.coef','p-val'])

# SEARCH THROUGH CHOSEN DIRECTORY STRUCTURE
# for data and calibration files
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
            assert len(c_lst)==1, "more than one calibration file in directory: {}".format(root)
            # open calibration file
            c_pth = os.path.join(root,c_lst[0])
            with open(c_pth,'rb') as fptr:
                cal_dat = pickle.load(fptr, fix_imports=False)
            # DO SOMETHING WITH CALIB DATA HERE ***
            print(cal_dat['details'])
        # look for cop data file using reg expression
        d_lst = list(filter(cop_re_o.match,files))
        if d_lst:
            # if list d_lst is not empty..
            # DO SOMETHING WITH DATA FILES HERE ***
            pass
