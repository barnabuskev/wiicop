#!/usr/bin/env python3
# To test a single loop of the acquisition series loop. No timer functionality to begin with

import pyudev
import xwiimote
import errno
import select
import sys
import os
import time
from subprocess import run
import numpy as np
from scipy import stats
import pandas as pd
import pickle
import configparser
from WiiCopFunctions import *
# from WiiCopFunctions import (get_sessionname, txtmenu, listdirs,
#     get_acq_info, connectBB, calcCOP, procBBdata, getnsamp, validcode)
from datetime import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# user defined options
# ~~~~~~~~~~~~~~~~~~~~
# sample size for calibration
smp_size = 50
# outlier z-score threshold defined here
out_thresh = 3
# percentage zeros %age max limit defined here
maxpcnt = 5
# Pandas series to define calibration weights
# calib_wgts = pd.Series({0:5,1:10,2:18})
calib_wgts = pd.Series({0:5,1:9,2:16.5})
# calibration units ('Kgs' or 'lbs')
# calib_units = 'lbs'
calib_units = 'Kgs'
# set the time interval for FuncAnimation (milliseconds)
anim_interval = 100

# constants
# ~~~~~~~~~
# dictionary for enumeration of sensors
SENS_DCT = {0:'Top right',1:'Bottom right',2:'Top left',3:'Bottom left'}
# number of sensors
N_S = 4
# lbs to kgs conversion factor
LBS2KGS = 0.453592
# Balance board dimensions width and length in mm (Leach, J.M., Mancini, M., Peterka, R.J., Hayes,
# T.L. and Horak, F.B., 2014. Validating and calibrating the Nintendo Wii
# balance board to derive reliable center of pressure measures. Sensors,
# 14(10), pp.18244-18267.)
BB_Y = 238
BB_X = 433

# define acquisition object
class acq_object:
    'object to implement plotting data in animation loop, storage and saving data'

    def __init__(self,aqc_info,sesh_path,bb,cal_mod):
        # aqc_info: dictionary of acquisition specific info
        # sesh_path: path to session directory
        # bb: a pyudev device object for balance board
        # cal_mod: calibration model
        # create new variables and arrays
        # create numpy array to store data initially from board
        self.tmp_dat = np.empty((1,N_S))
        # create numpy array to accumulate raw sensor_data
        self.sens_dat = np.empty((0,N_S))
        # create numpy array to store sensor acq time data
        self.time_dat = np.empty((0,2))
        # create numpy array to store COP data
        self.cop_dat = np.empty((0,2))
        # store session path
        self.sesh_path = sesh_path
        # create var to store save start time
        save_start = 0
        # create var to store save end time
        save_end = 0
        # set save data to file flag
        self.savedatf = False
        # set store data to array flag
        self.storedat = False
        # input acquisition info
        self.acq_info = aqc_info
        # create polling object
        self.p_obj = select.poll()
        # create xwiimote bboard device
        self.bbdev = xwiimote.iface(bb.sys_path)
        # register bbdev to pollong object
        self.p_obj.register(self.bbdev.get_fd(), select.POLLIN)
        # open bb device
        self.bbdev.open(xwiimote.IFACE_BALANCE_BOARD)
        # event structure
        self.revt = xwiimote.event()
        # calibration model
        self.cal_mod = cal_mod

    def animate(self,cop_i):
        polls = self.p_obj.poll()
        for fd, evt in polls:
            try:
                self.bbdev.dispatch(self.revt)
                # read each sensor
                for i_s in range(N_S):
                    # get the 'x' data from the Absolute Motion Payload for each sensor
                    self.tmp_dat[0,i_s] = self.revt.get_abs(i_s)[0]
                # get COP
                cop_p = calcCOP(self.tmp_dat,self.cal_mod,BB_X,BB_Y)
                # plot cop
                scat.set_offsets(cop_p)
                if self.storedat:
                    # save data in arrays...
                    # cop data
                    self.cop_dat = np.vstack((self.cop_dat,cop_p))
                    # event time
                    self.time_dat = np.vstack((self.time_dat,np.array(self.revt.get_time())))
                    # raw sensor data
                    self.sens_dat = np.vstack((self.sens_dat,self.tmp_dat))
            except IOError as e:
                # do nothing if resource unavailable
                if e.errno != errno.EAGAIN:
                    print(e)
    def save_bbdat(self):
        # called to put data in dictionary & save as a pickled binary file
        bbdat = {'rawsens':self.sens_dat,'timedat':self.time_dat,'cop':self.cop_dat}
        # get save file name...
        sfn = self.aqc_name()+'.dat'
        sfn = os.path.join(self.sesh_path,sfn)
        with open(sfn,'wb') as fptr:
            pickle.dump(bbdat,fptr)
    def aqc_name(self):
        # returns a string for labelling acquisition and for file name
        tmp = self.acq_info.copy()
        afn = 'subj'
        afn = afn+tmp.pop('subject_code')
        acqt = tmp.pop('acq_time')
        for iks in tmp.values():
            afn = afn+'_'+iks
        if acqt!='inf':
            afn = afn+'_'+acqt
        return afn
    def shutdown(self):
        # close device
        self.bbdev.close(xwiimote.IFACE_BALANCE_BOARD)
        self.p_obj.unregister(self.bbdev.get_fd())


# to suppress the annoying warning
import warnings
warnings.filterwarnings('ignore')
# clear terminal
run('clear')

# connect to balance board and exit if none connected
bb = connectBB()
if bb==None:
    time.sleep(5)
    print('Exiting')
    sys.exit()


# SELECT STUDY
# ~~~~~~~~~~~~
# select study and read config file
# get current script dir
script_dir = os.path.dirname(os.path.realpath(__file__))
# get config directory
config_dir = os.path.join(script_dir,'config_files')
# Get list of config files in config_dir
config_files_t = os.listdir(config_dir)
# select config files using list comprehension
config_files = [x for x in config_files_t if '.config' in x]
# use config parser to read each config file for names of study
s_names = list()
config_tmp = configparser.ConfigParser()
for i_f in config_files:
    cf = os.path.join(config_dir,i_f)
    config_tmp.read(cf)
    s_names.append(config_tmp['study info']['study_name'])
# user interface to get user selection
del(config_tmp)
chc = txtmenu('Select study',s_names)
# read selected config file
config = configparser.ConfigParser()
config.read(os.path.join(config_dir,config_files[chc]))

# SETUP SESSION
# ~~~~~~~~~~~~~
# get path of study directory
std_dir = config['study info']['study_dir']
# get path of session directory...
# read all names of all sessions in study directory
prev_sesh = listdirs(std_dir)
# default name for session
tmnow = datetime.now()
def_name = tmnow.strftime("%b_%d_%Y_%p")
s_dir_nm = get_sessionname(prev_sesh,def_name)
# check if session dir already exists
if s_dir_nm in prev_sesh:
    print('Session already exists. Start again and choose another name')
    time.sleep(5)
    sys.exit()
# session path
sesh_path = os.path.join(std_dir,s_dir_nm)
# create directory
os.mkdir(sesh_path,mode=0o775)


# CALIBRATE BOARD
# ~~~~~~~~~~~~~~~
# preallocate array for mean of sensor readings for each calibration weight
n_calib = len(calib_wgts)
sens_mean = np.empty([N_S,n_calib])
print('\n\nStarting calibration sequence...\nApply weights as close as possible to the centre...\n')
for i_ws in range(n_calib):
    print('Apply',str(calib_wgts[i_ws]),calib_units,'to balance board\n')
    input_str = input('Press return when ready...\n\n')
    # read data
    sens_dat = procBBdata(bb, getnsamp, smp_size)
    # print(sens_dat)
    # for each sensor...
    for i_s in range(N_S):
        sens_dat1 = sens_dat[:,i_s]
        # print out percentage of readings == 0
        prctzero = sum(sens_dat1==0)/smp_size*100
        if prctzero > 0:
            print('Warning: percentage zeros for {0} sensor = {1:.2f}%'.format(SENS_DCT[i_s],prctzero))
        # detect if all values are for sensor are zero
        if prctzero > maxpcnt:
            print('Error: percentage zeros for {0} sensor exceeds maximum ({1:.2f}%).'.format(SENS_DCT[i_s],prctzero))
            print('Use heavier weight or move board to another location.')
            print('Exiting')
            time.sleep(5)
            sys.exit()
        else:
            # get zscores for sensor
            zscrs = stats.zscore(sens_dat1)
            # replace those outside threshold with nans
            sens_dat1[np.absolute(zscrs) > out_thresh] = np.nan
            # get mean excluding nans.
            sens_mean[i_s,i_ws] = np.nanmean(sens_dat1)
# For each sensor get a linear model to calibrate data...
# create dictionary to store results to file and array for model parameters
# 'm'-slopes,'c'-intercepts, 'p'-p-values, 'r'- r values, 'se' -standard errors
# cal_mod row zero = slopes, row 1 = intercepts. Each col represents a sensor
# Calibration weights are divided by number of sensors
cal_mod = np.empty([2,N_S])
cal_dat = dict()
dc = dict()
for i_s in range(N_S):
    cal_m, cal_c, cal_r, cal_p, cal_se = stats.linregress(sens_mean[i_s,:],calib_wgts.values/N_S)
    # store results to dictionary
    dc.update({'m':cal_m})
    dc.update({'c':cal_c})
    dc.update({'r':cal_r})
    dc.update({'p':cal_p})
    dc.update({'se':cal_se})
    # store model parameters to an array
    cal_mod[0,i_s] = cal_m
    cal_mod[1,i_s] = cal_c
    cal_dat.update({SENS_DCT[i_s]:dc})
# save calibration data in session directory
calib_dat = {'model':cal_mod, 'details':cal_dat}
cfn = os.path.join(sesh_path,'calibration_dat')
with open(cfn,'wb') as fptr:
    pickle.dump(calib_dat,fptr)
print('Remove calibration weights from balance board\n\n')
##TEST overide calibration
#cal_mod = np.array([[0.01776906,0.01645395,0.02366412,0.02252513],[ 0.39208467,-0.7261971,-0.05245845,-3.55288195]])


# GET SERIES OF ACQUISITIONS
loop_flag = True
while loop_flag:
    # Get acquisition info
    # {'group': 'case', 'acq_time': 'inf', 'subject_code': '121', 'epoch': 'before'}
    acq_info = get_acq_info(config)
    # get acquisition time in milliseconds if timed
    if acq_info['acq_time'] != 'inf':
        acq_time_ms = int(acq_info['acq_time'])*1000
    # create acq_object instance
    acqobj = acq_object(acq_info,sesh_path,bb,cal_mod)
    # CREATE WINDOW
    # Initial instructions
    text_start = 'Press Spacebar to start recording'
    text_stop = 'Press Spacebar to stop recording'
    # remove toolbar
    mpl.rcParams['toolbar'] = 'None'
    # Create new figure and an axes which fills it...
    # set figure width in inches
    fig_width = 12
    # set fig ratio based on size of bboard rectange whose corners are sensors
    fig = plt.figure(figsize=(fig_width, fig_width*BB_Y/BB_X))
    fig.canvas.set_window_title(acqobj.aqc_name())
    # frameon determines whether background of frame will be drawn
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.set_xlim(-BB_X/2, BB_X/2), ax.set_xticks([])
    ax.set_ylim(-BB_Y/2, BB_Y/2), ax.set_yticks([])
    # create a scatter object at initial position 0,0
    cop_x = 0
    cop_y = 0
    scat = ax.scatter(cop_x, cop_x, s=200, lw=0.5, facecolors='green')
    # create text box
    text_h = ax.text(0.02, 0.98, text_start, verticalalignment='top',horizontalalignment='left',
     transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='white'), gid = 'notrec')
    # define keypress event handler
    def onkeypress(evt):
        if evt.key==' ':
            # spacebar pressed
            if text_h.get_gid()=='notrec':
                # not recording data...
                # change colour of dot
                scat.set_facecolors('red')
                plt.draw()
                # set gid to recording to flag recording state
                text_h.set_gid('rec')
                if acq_info['acq_time'] != 'inf':
                    # timed acquisition - start timer
                    acq_timer.start()
                    text_h.set_text('Timed acquisition')
                    # set acquisition object to store data in array
                    acqobj.storedat = True
                else:
                    # manual acq
                    # change instructions
                    text_h.set_text(text_stop)
                    # set acquisition object to store data in array
                    acqobj.storedat = True
            elif text_h.get_gid()=='rec':
                if acq_info['acq_time'] != 'inf':
                    # timed acq - do nothing
                    pass
                else:
                    # recording data, manual acq
                    acqobj.storedat = False
                    acqobj.savedatf = True
                    plt.close()
            else:
                print('error in onkeypress - unrecognised text_h gid')
    def t_event():
        # callback function for timer
        acqobj.storedat = False
        acqobj.savedatf = True
        acq_timer.remove_callback(t_event)
        plt.close()
    # create timer object
    if acq_info['acq_time'] != 'inf':
        acq_timer = fig.canvas.new_timer(interval=acq_time_ms)
        acq_timer.add_callback(t_event)
    # attach keypress event handler to figure canvas
    cid = fig.canvas.mpl_connect('key_press_event', onkeypress)
    # PLOT ANIMATION - interval can't be too small or it gives an attribute error
    animation = FuncAnimation(fig, acqobj.animate, interval=anim_interval)
    plt.show()
    # save data if flag = True
    print(acqobj.savedatf)
    if acqobj.savedatf:
        acqobj.save_bbdat()
        print('\nSession {}:'.format(s_dir_nm))
        print('  Data has been saved in file {}\n'.format(acqobj.aqc_name()+'.dat'))
    else:
        print('\nNo data has been saved in this acquisition\n')
    # shutdown devices
    acqobj.shutdown()
    # ask user if they wish to do another acquisition
    chc = input('Get another acquisition? (y/n)\n')
    if chc in ['y','Y']:
        pass
        # clear terminal
        #run('clear')
    else:
        loop_flag = False
        # clear terminal
        # run('clear')

# END OF ACQUISITION LOOP
