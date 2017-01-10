#!/usr/bin/env python3
# software to convert raw centre of pressure (COP) data into various COP based measures of balance


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
import numpy as np
import pandas as pd
import configparser
import matplotlib.pyplot as plt
import matplotlib
import COPparamsFs as cp
# %matplotlib inline



# INITIALISE
# set regular expression to find calibration file
cal_re = "calib.*dat"
# set regular expression to find cop data file
cop_re = "subj.*.dat"
# specify list of cop parameters
cop_params = ['pred_ellipse','path_length','velocity']
# string that signifies subject code
sbjstr = 'subj'
# Display stabilogram flag
disps_f = False
# Save stabilogram flag
saves_f = False
# name of image directory
imdir = "stabilograms"
# Balance board dimensions width and length in mm (Leach, J.M., Mancini, M., Peterka, R.J., Hayes,
# T.L. and Horak, F.B., 2014. Validating and calibrating the Nintendo Wii
# balance board to derive reliable center of pressure measures. Sensors,
# 14(10), pp.18244-18267.)
BB_Y = 238
BB_X = 433
# filter parameters...
# cutoff frequency as proportion of Nyquist
cutoff = 2/3
# order of Butterworth filter
order = 4

# set up if plots flagged
if disps_f or saves_f:
    matplotlib.rcParams['toolbar'] = 'None'
    # create empty list to store stuff to plot
    plt_lst = []
    # create figure and axis
    fig,ax = plt.subplots(1)
    fig.canvas.set_window_title('Stabilogram')
if saves_f:
    os.mkdir(imdir)

# setup regular expression objects
cal_re_o = re.compile(cal_re)
cop_re_o = re.compile(cop_re)

# create empty pandas dataframes to store calibration and cop data
cal_df=pd.DataFrame(columns=['session','sensor','slope','slope.se','r.coef','p-val'])
# change to $XDG_RUNTIME_DIR/gvfs where samba mounts its shares
gvfs_pth = os.environ['XDG_RUNTIME_DIR']+'/gvfs/'
os.chdir(os.path.dirname(gvfs_pth))
# Get user to choose config file
config_file = tk_fd.askopenfilename(title = 'Get config file for study',filetypes=[('Data files', '*.config'), ('All files','*')])
# move to directory above config file
os.chdir(os.path.dirname(config_file))
os.chdir("..")
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

            # Store 1 row of calibration data...
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
            for fi in d_lst:
                # for each data file..

                # store row of study metadata...
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


                # read COP data
                d_pth = os.path.join(root,fi)
                with open(d_pth,'rb') as fptr:
                    pkl = pickle.load(fptr)
                # convert time data into seconds
                t_dat = pkl['timedat']
                t_dat = t_dat[:,0] + t_dat[:,1]/1000000
                # reshape t_dat so that it is an nd array with one singleton dimension
                t_dat = np.reshape(t_dat,(t_dat.size,-1))
                # add time data to cop data
                cop_dat = np.concatenate((pkl['cop'],t_dat), axis=1)

                # Preprocess COP data
                # resample to even sample points
                cop_dat_r = cp.resamp(cop_dat)
                # low pass filtering
                cop_dat_f = cp.bfilt(cop_dat_r, cutoff, order)
                # # TEST ***
                # # plot coronal
                # fg, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
                # # resampled or raw
                # ax1.plot(cop_dat[:,2],cop_dat[:,0],'bo-')
                # # ax1.plot(t,cor,'bo-')
                # ax1.set_xlabel('time (secs)')
                # ax1.set_ylabel('coronal plane')
                # ax1.set_title('Raw data')
                # ax1.grid()
                # # resampled and filtered
                # ax2.plot(cop_dat_f[:,2],cop_dat_f[:,0],'bo-')
                # ax2.set_xlabel('time (secs)')
                # ax2.set_title('Resampled and filtered')
                # ax2.grid()
                # mng = plt.get_current_fig_manager()
                # mng.resize(*mng.window.maxsize())
                # plt.show()
                # # ***

                # Get COP parameters...
                # 95% Prediction interval
                cop_df.ix[nxt_cop,'pred_ellipse'] = cp.PI95(cop_dat_f)
                # path length
                pl = cp.pathl(cop_dat)
                cop_df.ix[nxt_cop,'path_length'] = pl
                # velocity
                cop_df.ix[nxt_cop,'velocity'] = pl/int(cop_df.ix[nxt_cop,'acq_time'])

                # store data for plotting if flagged
                if disps_f or saves_f:
                    # create a dictionary of relevant study factors
                    std_fct = {}
                    std_fct['subj'] = scode
                    for fct_i in fct_lst:
                        for lev in lev_lst:
                            if lev in config['factors'][fct_i]:
                                std_fct[fct_i] = lev
                    plt_lst.append([[cop_dat, std_fct]])

# Plot stabilograms (see Scoppa2013) if flagged
if disps_f or saves_f:
    ax.axis([-BB_X/2, BB_X/2, -BB_Y/2, BB_Y/2])
    ax.grid()
    plot1 = True
    plt.ion()
    for ia in plt_lst:
        if plot1:
            line_h, = ax.plot(ia[0][0][:,0], ia[0][0][:,1],'b-')
            plot1 = False
        else:
            line_h.set_xdata(ia[0][0][:,0])
            line_h.set_ydata(ia[0][0][:,1])
        plt.title('Subject: '+ia[0][1]['subj'])
        # get factors string
        fct_str = ""
        for ib in fct_lst:
            fct_str = fct_str + ib + ": " + ia[0][1][ib] + ", "
        fct_str = fct_str.rstrip(", ")
        txt_h = plt.text(-200,100,fct_str, fontsize=14)
        if disps_f:
            plt.show()
            plt.pause(0.5)
        if saves_f:
            # create file name
            im_file = ".png"
            for ib in fct_lst:
                im_file = ia[0][1][ib] + im_file
            im_file = "subj" + ia[0][1]['subj'] + "_" + im_file
            plt.savefig(os.path.join(imdir,im_file))
        txt_h.remove()


# create results directory if it doesn't exist
res_dir = os.path.join(seshd,'results')
if not(os.path.isdir(res_dir)):
    os.mkdir(res_dir)
# write calibration results
calib_file = os.path.join(res_dir,'calib_results.csv')
cal_df.to_csv(calib_file)
# write study results
study_file = os.path.join(res_dir,'study_results.csv')
cop_df.to_csv(study_file)
