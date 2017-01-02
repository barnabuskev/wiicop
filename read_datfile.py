#!/usr/bin/env python3
# to read a pickled file into memory
import tkinter.filedialog as tk_fd
import pickle
import numpy as np
import sys
import matplotlib.pyplot as plt
from scipy import signal
from scipy.interpolate import interp1d
import math

doplots = True
savecsv = False

dfile = tk_fd.askopenfilename(title = 'Get pickled data file',filetypes=[('Data files', '*.dat'), ('All files','*')])
if not dfile:
    print('No file chosen')
    sys.exit(0)
with open(dfile,'rb') as fptr:
    dc = pickle.load(fptr, fix_imports=False)
# convert time data into seconds
#t_dat = dc['timedat'].astype(int)
t_dat = dc['timedat']
# print(t_dat)
# print(t_dat[:,1]/1000000)
t_dat = t_dat[:,0] + t_dat[:,1]/1000000
# reshape t_dat so that it is an nd array with one singleton dimension
t_dat = np.reshape(t_dat,(t_dat.size,-1))
# subtract the first time value from all
t_dat = np.subtract(t_dat,t_dat[0])
# add time data to cop data
bb_dat = np.concatenate((dc['cop'],t_dat), axis=1)
n_samp = bb_dat.shape[0]
# add raw sensor data
bb_dat = np.concatenate((bb_dat,dc['rawsens']), axis=1)
# save each numpy array as a CSV file...
if savecsv:
    fname = tk_fd.asksaveasfilename(title='Choose file name to save BB data', filetypes=[('CSV files', '.csv'), ('all files', '.*')])
    if fname:
        np.savetxt(fname,bb_dat, delimiter=',', header='copX,copY,time,TopR,BotR,TopL,BotL', comments='')
# plot statokinesiogram - coronal plane using time as x-axis
if doplots:

    # resample data
    t = np.linspace(bb_dat[0,2], bb_dat[-1,2], num=n_samp, endpoint=True)
    f_cor = interp1d(bb_dat[:,2], bb_dat[:,0], kind='linear')
    cor = f_cor(t)
    f_sag = interp1d(bb_dat[:,2], bb_dat[:,1], kind='linear')
    sag = f_sag(t)

    # Butterworth filter
    order = 4
    # -3dB cutoff freq proportion of Nyquist freq (half sampling freq)
    cutoff = 2/3
    b,a = signal.butter(order, cutoff)
    # filter coronal
    cor_lp = signal.filtfilt(b, a, cor)
    print(len(cor))
    print(len(cor_lp))
    # filter sagittal
    sag_lp = signal.filtfilt(b, a, sag)

    # plot coronal
    fg, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    # resampled or raw
    ax1.plot(bb_dat[:,2],bb_dat[:,0],'bo-')
    # ax1.plot(t,cor,'bo-')
    ax1.set_xlabel('time (secs)')
    ax1.set_ylabel('coronal plane')
    ax1.grid()
    # filtered
    ax2.plot(t,cor_lp,'bo-')
    ax2.set_xlabel('time (secs)')
    ax2.grid()
    plt.show()

    # plot sagittal
    fg, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    # resampled or raw
    ax1.plot(bb_dat[:,2],bb_dat[:,1],'bo-')
    # ax1.plot(t,sag,'bo-')
    ax1.set_xlabel('time (secs)')
    ax1.set_ylabel('coronal plane')
    ax1.grid()
    # filtered
    ax2.plot(t,sag_lp,'bo-')
    ax2.set_xlabel('time (secs)')
    ax2.grid()
    plt.show()
