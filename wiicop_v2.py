#!/usr/bin/env python3
# to test speed of wii board data acquisition

import os
import sys
from subprocess import run
import time
import threading
from queue import Queue
import errno
import numpy as np
import pandas as pd
import pyudev
import xwiimote
import select
import configparser
from WiiCopFunctions import connectBB, calcCOP, procBBdata, txtmenu,\
get_sessionname, listdirs, get_acq_info, getnsamp, validcode
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
anim_interval = 50

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


# FUNCTION DEFINITIONS
def aqc_name(acq_info):
    # This is returns a string for labelling acquisition and for file name
    tmp = acq_info.copy()
    afn = 'subj'
    afn = afn+tmp.pop('subject_code')
    acqt = tmp.pop('acq_time')
    for iks in tmp.values():
        afn = afn+'_'+iks
    if acqt!='inf':
        afn = afn+'_'+acqt
    return afn

# CLASS DEFINITIONS
# create a class based on threading.thread
class wii_thread(threading.Thread):
    def __init__ (self,bb,cal_mod,BB_X,BB_Y):
        threading.Thread.__init__(self)
        self.runflag = True
        self.storeflag = False
        self.n_s = 4
        self.bbdev = xwiimote.iface(bb.sys_path)
        self.p = select.poll()
        self.p.register(self.bbdev.get_fd(), select.POLLIN)
        # open bb device
        self.bbdev.open(xwiimote.IFACE_BALANCE_BOARD)
        # create xwiimote event structure
        self.revt = xwiimote.event()
        # create numpy array to store data from board
        self.tmp_dat = np.empty((1,self.n_s))
        self.cop = np.empty((1,2))
        self.cop_dat = np.empty((0,2))
        self.cal_mod = cal_mod
        self.BB_X = BB_X
        self.BB_Y = BB_Y

    def run(self):
        lock.acquire()
        runflag = self.runflag
        lock.release()
        while runflag:
            polls = self.p.poll()
            try:
                self.bbdev.dispatch(self.revt)
                tdat = self.revt.get_time()
                for i_s in range(self.n_s):
                    self.tmp_dat[0,i_s] = self.revt.get_abs(i_s)[0]
                self.cop = calcCOP(self.tmp_dat,self.cal_mod,self.BB_X,self.BB_Y)
                lock.acquire()
                storeflag = self.storeflag
                lock.release()
                if storeflag:
                    wii_q.put(np.concatenate((self.cop,np.array(tdat))))
            except IOError as e:
                # do nothing if resource unavailable
                if e.errno != errno.EAGAIN:
                    print(e)
                    self.p.unregister(self.bbdev.get_fd())
            lock.acquire()
            runflag = self.runflag
            lock.release()
        # close down BB interface
        self.bbdev.close(xwiimote.IFACE_BALANCE_BOARD)
        self.p.unregister(self.bbdev.get_fd())


class plot_cop:
    'object to implement plotting cop data in animation loop'

    def __init__(self,aqc_info,BB_X,BB_Y):
        self.acq_info = aqc_info
        # Initial instructions
        self.text_start = 'Press Spacebar to start recording'
        self.text_stop = 'Press Spacebar to stop recording'
        # remove toolbar
        mpl.rcParams['toolbar'] = 'None'
        # Create new figure and an axes which fills it...
        # set figure width in inches
        fig_width = 12
        # set fig ratio based on size of bboard rectange whose corners are sensors
        self.fig = plt.figure(figsize=(fig_width, fig_width*BB_Y/BB_X))
        self.fig.canvas.set_window_title(aqc_name(self.acq_info))
        # frameon determines whether background of frame will be drawn
        ax = self.fig.add_axes([0, 0, 1, 1], frameon=False)
        ax.set_xlim(-BB_X/2, BB_X/2), ax.set_xticks([])
        ax.set_ylim(-BB_Y/2, BB_Y/2), ax.set_yticks([])
        # create a scatter object at initial position 0,0
        self.scat = ax.scatter(0, 0, s=200, lw=0.5, facecolors='green')
        # create text box
        self.text_h = ax.text(0.02, 0.98, self.text_start, verticalalignment='top',horizontalalignment='left',
        transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='white'), gid = 'notrec')
        # create timer object
        if self.acq_info['acq_time'] != 'inf':
            acq_time_ms = int(self.acq_info['acq_time'])*1000
            self.acq_timer = self.fig.canvas.new_timer(interval=acq_time_ms)
            self.acq_timer.add_callback(self.t_event)
        # attach keypress event handler to figure canvas
        self.fig.canvas.mpl_connect('key_press_event', self.onkeypress)

    def animate(self,cop_i):
        # plot COP
        lock.acquire()
        cop = thd.cop
        lock.release()
        self.scat.set_offsets(cop)

    # Keypress event handler
    def onkeypress(self,evt):
        if evt.key==' ':
            # spacebar pressed
            if self.text_h.get_gid()=='notrec':
                # start recording data...
                # change colour of dot
                self.scat.set_facecolors('red')
                plt.draw()
                # set gid to recording to flag recording state
                self.text_h.set_gid('rec')
                if self.acq_info['acq_time'] != 'inf':
                    # timed acquisition - start timer
                    self.acq_timer.start()
                    self.text_h.set_text('Timed acquisition')
                else:
                    # manual acq
                    # change instructions
                    self.text_h.set_text(self.text_stop)
                # set thread to store data in queue
                lock.acquire()
                thd.storeflag = True
                lock.release()

            elif self.text_h.get_gid()=='rec':
                # stop recording
                if self.acq_info['acq_time'] != 'inf':
                    # timed acq - do nothing
                    pass
                else:
                    # recording data, manual acq
                    lock.acquire()
                    thd.storeflag = False
                    thd.runflag = False
                    lock.release()
                    plt.close()
            else:
                print('error in onkeypress - unrecognised text_h gid')

    # callback function for timer
    def t_event(self):
        # stop thread queuing data and stop it running
        lock.acquire()
        thd.storeflag = False
        thd.runflag = False
        lock.release()
        self.acq_timer.remove_callback(self.t_event)
        plt.close()


# ~~~~~~~~~~~~~~~
# MAIN ROUTINE
# ~~~~~~~~~~~~~~~

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
# get directories
script_dir = os.path.dirname(os.path.realpath(__file__))
config_dir = os.path.join(script_dir,'config_files')

# Get list of config files in config_dir
config_files_t = os.listdir(config_dir)
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


# # CALIBRATE BOARD
# # ~~~~~~~~~~~~~~~
# # preallocate array for mean of sensor readings for each calibration weight
# n_calib = len(calib_wgts)
# sens_mean = np.empty([N_S,n_calib])
# print('\n\nStarting calibration sequence...\nApply weights as close as possible to the centre...\n')
# for i_ws in range(n_calib):
#     print('Apply',str(calib_wgts[i_ws]),calib_units,'to balance board\n')
#     input_str = input('Press return when ready...\n\n')
#     # read data
#     sens_dat = procBBdata(bb, getnsamp, smp_size)
#     # print(sens_dat)
#     # for each sensor...
#     for i_s in range(N_S):
#         sens_dat1 = sens_dat[:,i_s]
#         # print out percentage of readings == 0
#         prctzero = sum(sens_dat1==0)/smp_size*100
#         if prctzero > 0:
#             print('Warning: percentage zeros for {0} sensor = {1:.2f}%'.format(SENS_DCT[i_s],prctzero))
#         # detect if all values are for sensor are zero
#         if prctzero > maxpcnt:
#             print('Error: percentage zeros for {0} sensor exceeds maximum ({1:.2f}%).'.format(SENS_DCT[i_s],prctzero))
#             print('Use heavier weight or move board to another location.')
#             print('Exiting')
#             time.sleep(5)
#             sys.exit()
#         else:
#             # get zscores for sensor
#             zscrs = stats.zscore(sens_dat1)
#             # replace those outside threshold with nans
#             sens_dat1[np.absolute(zscrs) > out_thresh] = np.nan
#             # get mean excluding nans.
#             sens_mean[i_s,i_ws] = np.nanmean(sens_dat1)
#
# # For each sensor get a linear model to calibrate data...
# # create dictionary to store results to file and array for model parameters
# # 'm'-slopes,'c'-intercepts, 'p'-p-values, 'r'- r values, 'se' -standard errors
# # cal_mod row zero = slopes, row 1 = intercepts. Each col represents a sensor
# # Calibration weights are divided by number of sensors
# cal_mod = np.empty([2,N_S])
# cal_dat = dict()
# dc = dict()
# for i_s in range(N_S):
#     cal_m, cal_c, cal_r, cal_p, cal_se = stats.linregress(sens_mean[i_s,:],calib_wgts.values/N_S)
#
#     # store results to dictionary
#     dc.update({'m':cal_m})
#     dc.update({'c':cal_c})
#     dc.update({'r':cal_r})
#     dc.update({'p':cal_p})
#     dc.update({'se':cal_se})
#
#     # store model parameters to an array
#     cal_mod[0,i_s] = cal_m
#     cal_mod[1,i_s] = cal_c
#     cal_dat.update({SENS_DCT[i_s]:dc})
#
# # save calibration data in session directory
# calib_dat = {'model':cal_mod, 'details':cal_dat}
# cfn = os.path.join(sesh_path,'calibration_dat')
# with open(cfn,'wb') as fptr:
#     pickle.dump(calib_dat,fptr)
# print('Remove calibration weights from balance board\n\n')

#TEST overide calibration
cal_mod = np.array([[0.01776906,0.01645395,0.02366412,0.02252513],[ 0.39208467,-0.7261971,-0.05245845,-3.55288195]])

# GET SERIES OF ACQUISITIONS
loop_flag = True

# set up objects for data acquisition
lock = threading.Lock()
wii_q = Queue(maxsize=0)


while loop_flag:

    # Get acquisition info
    # {'group': 'case', 'acq_time': 'inf', 'subject_code': '121', 'epoch': 'before'}
    acq_info = get_acq_info(config)

    # create plot_cop instance
    pltcop_obj = plot_cop(acq_info,BB_X,BB_Y)
    thd = wii_thread(bb,cal_mod,BB_X,BB_Y)

    # Start thread
    thd.start()

    # PLOT ANIMATION - interval can't be too small or it gives an attribute error
    animation = FuncAnimation(pltcop_obj.fig, pltcop_obj.animate,interval=anim_interval)
    plt.show()

    thd.join()

    # get data from queue and write to file
    acq_data = np.empty((0,4))
    while not(wii_q.empty()):
        acq_data = np.vstack((acq_data,wii_q.get()))
    #***
    print(acq_data.shape)

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
