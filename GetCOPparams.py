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
import configparser
import matplotlib.pyplot as plt
# %matplotlib inline
# next line assumes hyperellipsoid.py is in same directory
from hyperellipsoid import hyperellipsoid


# INITIALISE
# set regular expression to find calibration file
cal_re = "calib.*dat"
# set regular expression to find cop data file
cop_re = "subj.*.dat"
# specify list of cop parameters
cop_params = ['pred_ellipse','path_length']
# string that signifies subject code
sbjstr = 'subj'

# setup regular expression objects
cal_re_o = re.compile(cal_re)
cop_re_o = re.compile(cop_re)

# create empty pandas dataframes to store calibration and cop data
cal_df=pd.DataFrame(columns=['session','sensor','slope','slope.se','r.coef','p-val'])
# Get user to choose config file
config_file = tk_fd.askopenfilename(title = 'Get config file for study',filetypes=[('Data files', '*.config'), ('All files','*')])
# read selected config file
config = configparser.ConfigParser()
config.read(config_file)
# get info list of factors
fct_lst = config.options('factors')
cop_df=pd.DataFrame(columns=['session','subj'] + fct_lst + cop_params)


# SEARCH THROUGH CHOSEN DIRECTORY STRUCTURE
# for data and calibration files
seshd = tk_fd.askdirectory(title = 'Open study directory containing sessions')
if not seshd:
    sys.exit()
for root, dirs, files in os.walk(seshd):
    # for each directory
    if len(files) > 0:
        # do stuff with files if dir contains any
        # look for calibration file using reg expression
        c_lst = list(filter(cal_re_o.match,files))
        if c_lst:
            # if list c_lst is not empty..
            # should contain only one calibration file
            assert len(c_lst)==1, "more than one calibration file in directory: {}".format(root)
            # open calibration file
            c_pth = os.path.join(root,c_lst[0])
            with open(c_pth,'rb') as fptr:
                tmp = pickle.load(fptr, fix_imports=False)
            # DO SOMETHING WITH CALIB DATA HERE ***
            cal_dat = tmp['details']
            nxt_cal = len(cal_df.index)
            s_ind = 0
            for sns in cal_dat.keys():
                # for each sensor..
                # create empty row
                cal_df.loc[nxt_cal+s_ind] = None
                cal_df.ix[nxt_cal+s_ind,'session'] = os.path.basename(root)
                cal_df.ix[nxt_cal+s_ind,'sensor'] = sns
                cal_df.ix[nxt_cal+s_ind,'slope'] = cal_dat[sns]['m']
                cal_df.ix[nxt_cal+s_ind,'slope.se'] = cal_dat[sns]['se']
                cal_df.ix[nxt_cal+s_ind,'r.coef'] = cal_dat[sns]['r']
                cal_df.ix[nxt_cal+s_ind,'p-val'] = cal_dat[sns]['p']
                s_ind+=1
        # look for cop data file using reg expression
        d_lst = list(filter(cop_re_o.match,files))
        if d_lst:
            # if list d_lst is not empty..
            # DO SOMETHING WITH DATA FILES HERE ***
            for fi in d_lst:
                # for each data file..
                nxt_cop = len(cop_df.index)
                # create empty row
                cop_df.loc[nxt_cop] = None
                # strip extension
                prts = fi.split('.')
                # save levels as list
                lev_lst = prts[0].split('_')
                # get subject code
                tmp = [s for s in lev_lst if sbjstr in s]
                scode = tmp[0].strip(sbjstr)
                # convert to int then back to string with 3 leading zeros
                scode = int(scode)
                scode = str(scode).zfill(3)
                cop_df.ix[nxt_cop,'subj'] = scode
                # get session
                cop_df.ix[nxt_cop,'session'] = os.path.basename(root)
                # read study metadata into df
                for fct_i in fct_lst:
                    for lev in lev_lst:
                        if lev in config['factors'][fct_i]:
                            cop_df.ix[nxt_cop,fct_i] = lev
                # DO COP PROCESSING HERE

# write results to files
# TEST
print(cop_df.sort_values(['subj','side','trials']))
res_dir = os.path.join(seshd,'results')
if not(os.path.isdir(res_dir)):
    os.mkdir(res_dir)
calib_file = os.path.join(res_dir,'calib_file.csv')
cal_df.to_csv(calib_file)
