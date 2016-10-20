#!/usr/bin/env python3
# to read a pickled file into memory
import tkinter.filedialog as tk_fd
import pickle
import numpy as np

dfile = tk_fd.askopenfilename(title = 'Get pickled data file',filetypes=[('Data files', '*.dat'),
 ('All files','*')])
with open(dfile,'rb') as fptr:
    dc = pickle.load(fptr, fix_imports=False)
# convert time data into seconds
t_dat = dc['timedat']
t_dat = t_dat[:,0] + t_dat[:,1]/1000000
# reshape t_dat so that it is an nd array with one singleton dimension
t_dat = np.reshape(t_dat,(t_dat.size,-1))
# add time data to cop data
bb_dat = np.concatenate((dc['cop'],t_dat), axis=1)
# add raw sensor data
bb_dat = np.concatenate((bb_dat,dc['rawsens']), axis=1)
# save each numpy array as a CSV file...
fname = tk_fd.asksaveasfilename(title='Choose file name to save BB data', filetypes=[('CSV files', '.csv'), ('all files', '.*')])
# print(fname)
np.savetxt(fname,bb_dat, delimiter=',', header='copX,copY,time,TopR,BotR,TopL,BotL', comments='')
