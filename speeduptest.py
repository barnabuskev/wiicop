#!/usr/bin/env python3
# to test speed of wii board data acquisition

import pyudev
import xwiimote
import time
from WiiCopFunctions import *

smp_size = 1000

bb = connectBB()
if bb==None:
    time.sleep(5)
    sys.exit()

# read data
# time acquisition
t0 = time.time()
sens_dat = procBBdata(bb, getnsamp, smp_size)
t1 = time.time()
tdiff = t1-t0
srpersens = sens_dat.shape[0]/tdiff
print('Mean sample rate per sensor = {:.2f}'.format(srpersens))
