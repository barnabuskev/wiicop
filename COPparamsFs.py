# file to store functions that calculate COP parameters
# All functions need to input a cop data file, being a numpy array with 3
# columns: x-data, y-data, time (seconds)

# IMPORTS
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d
# Assumes hyperellipsoid.py is in same directory. Written by 'Marcos Duarte.
# https://github.com/demotu/BMC'
from hyperellipsoid import hyperellipsoid

def to_sing(arr):
    # converts array to an nd array with one singleton dimension
    arr = np.reshape(arr,(arr.size,-1))
    return arr

def nsamp(cop_dat):
    # get number of samples
    return cop_dat.shape[0]

def samp_rate(cop_dat):
    # get sample rate
    bg = cop_dat[0,-1]
    lst = cop_dat[-1,-1]
    tme = lst - bg
    nsmp = cop_dat.shape[0] - 1
    return nsmp/tme

def PI95(cop_dat):
    # get area of 95% prediction ellipse
    area, axes, angles, center, R = hyperellipsoid(cop_dat[:,(0,1)], units='mm', show=False)
    return area

def resamp(cop_dat):
    # resample data to even sample points using same average sample rate
    # resample data
    t = np.linspace(cop_dat[0,2], cop_dat[-1,2], num=nsamp(cop_dat), endpoint=True)
    f_cor = interp1d(cop_dat[:,2], cop_dat[:,0], kind='linear')
    cor = f_cor(t)
    f_sag = interp1d(cop_dat[:,2], cop_dat[:,1], kind='linear')
    sag = f_sag(t)
    # convert all to nd arrays
    cor = to_sing(cor)
    sag = to_sing(sag)
    t = to_sing(t)
    return np.concatenate((cor,sag,t),axis=1)

def bfilt(cop_dat, cutoff, order):
    # Butterworth filter
    b,a = signal.butter(order, cutoff)
    # filter coronal
    cor_lp = signal.filtfilt(b, a, cop_dat[:,0])
    # filter sagittal
    sag_lp = signal.filtfilt(b, a, cop_dat[:,1])
    return np.concatenate((to_sing(cor_lp),to_sing(sag_lp),to_sing(cop_dat[:,2])),axis=1)

def pathl(cop_dat):
    # to calculate COP path length
    delt = np.diff(cop_dat[:,(0,1)], axis = 0)
    sqs = np.square(delt)
    sum_s = np.add(sqs[:,0],sqs[:,1])
    lgths = np.sqrt(sum_s)
    return np.sum(lgths)
