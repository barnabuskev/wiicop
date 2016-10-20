# file to store functions for use by Wiicop.py

import pyudev
import xwiimote
import errno
import select
import sys
import os
import numpy as np
from tkinter import *
from tkinter import font
import string

# function to test if string is a valid subject code
def validcode(testnm):
    valid_chars='{}{}'.format(string.ascii_letters,string.digits)
    valid = True
    for c in testnm:
        if c not in valid_chars:
            valid = False
            break
    return valid

# function to obtain acquisition info: subject code, study factor levels, acquisition time
def get_acq_info(s_config):
    # function to obtain acquisition info: subject code, study factor levels, acquisition time
    # input: s_config:  config object for study
    # output: a dictionary with 2 compulsory keys: 'subject_code' and 'acq_time' and other keys being
    # the names of factors and they're associated chosen levels.
    # get subject code
    s_c = input('Enter subject code: ')
    while not validcode(s_c):
        print('\nOnly letters and numbers for subject codes\n')
        s_c = input('Enter subject code: ')
    fact_choices = {'subject_code':s_c}
    # get names of factors as a list
    fct_names = []
    for factor in s_config['factors']:
        fct_names.append(factor)
    # check if 'acq_time' is in list of factors
    if not 'acq_time' in fct_names:
        raise ValueError('Message from get_acq_info: There is no acq_time factor in the config file~~')
    # get factor levels
    for factor in s_config['factors']:
        levs = s_config['factors'][factor].split(',')
        if len(levs)==1:
            fact_choices.update({factor:levs[0]})
            continue
        tit_str = 'Choose level for {}'.format(factor)
        chc = txtmenu(tit_str,levs)
        fact_choices.update({factor:levs[chc]})
    return fact_choices

# returns device object for balance board
def connectBB():
    # returns sys path for balance board using evdev module
    context = pyudev.Context()
    # get list of devices matching devtype = 'balanceboard'
    devices = pyudev.Enumerator(context)
    tst = devices.match_attribute('devtype', 'balanceboard')
    # create empty list to store balance board info
    bboards = []
    # populate list
    for dfg in tst:
        bboards.append(dfg)
    # test how many bboards are connected - should be only one
    if len(bboards) == 0:
        print('No Wii balance boards found')
        return None
    if len(bboards) > 1:
        print('More than one Wii balance boards found: exiting')
        return None
    print('\nBalance board found!\n')
    # return the first in the list
    bb = bboards[0]
    return bb

# function to get data from BB and process it function 'func'
def procBBdata(bb, func, *args):
    # function to get data from BB and process it function 'func'
    # returns sens_dat that is an NX4 numpy array of raw sensor readings
    # each row a single data acquisition
    n_s = 4
    bbdev = xwiimote.iface(bb.sys_path)
    p = select.poll()
    p.register(bbdev.get_fd(), select.POLLIN)
    # open bb device
    bbdev.open(xwiimote.IFACE_BALANCE_BOARD)
    # create xwiimote event structure
    revt = xwiimote.event()
    # create numpy array to store data from board
    tmp_dat = np.empty((1,n_s))
    # creat another to accumulate all data
    sens_dat = np.empty((0,n_s))
    go_flg = True
    try:
        while go_flg:
            # waits here until event occurs
            polls = p.poll()
            for fd, evt in polls:
                try:
                    bbdev.dispatch(revt)
                    # revt.get_abs() takes an integer argument:
                    # 0 - top right when power button pointing towards you
                    # 1 - bottom right
                    # 2 - top left
                    # 3 - bottom left
                    for i_s in range(n_s):
                        tmp_dat[0,i_s] = revt.get_abs(i_s)[0]
                    # function that does something with sens_dat. Functions
                    # called by procBBdata must have parameters:
                    # go_flg, tmp_dat, sens_dat
                    go_flg, sens_dat = func(go_flg, tmp_dat, sens_dat, *args)
                except IOError as e:
                    # do nothing if resource unavailable
                    if e.errno != errno.EAGAIN:
                        print(e)
                        p.unregister(bbdev.get_fd())
    except KeyboardInterrupt:
        pass
    # cleaning
    bbdev.close(xwiimote.IFACE_BALANCE_BOARD)
    p.unregister(bbdev.get_fd())
    return sens_dat

# function to calibrate data and calculate COP
def calcCOP(indat,cal_mod,BB_X, BB_Y):
    # inputs: 'indat' a 1 X N_S numpy array of sensor measurements
    # 'cal_mod': a 2 X N_S numpy array, 1st row are scale values, 2nd row are offsets
    # BB_X, BB_Y - size of balance boad in mm
    cal_dat = indat * cal_mod[0,:]
    cal_dat += cal_mod[1,:]
    cal_dat = cal_dat.flatten()
    cop_x = BB_X/2*(cal_dat[0]+cal_dat[1]- (cal_dat[2]+cal_dat[3])) / (cal_dat[0]+cal_dat[1]+cal_dat[2]+cal_dat[3])
    cop_y = BB_Y/2*(cal_dat[0]+cal_dat[2]- (cal_dat[1]+cal_dat[3])) / (cal_dat[0]+cal_dat[1]+cal_dat[2]+cal_dat[3])
    return np.array([cop_x, cop_y])

# function to get n_samp samples from the wii board
def getnsamp(go_flg, tmp_dat, sens_dat, n_samp):
    # function to get n_samp samples from the wii board
    # functions called by procBBdata must have parameters:
    # go_flg, tmp_dat, sens_dat
    # if number of obtained samples less than n_samp..
    if sens_dat.shape[0] < n_samp:
        # get sensor data row
        sens_dat = np.vstack((sens_dat,tmp_dat))
    else:
        # flag end of data acquisition
        go_flg = False
    return go_flg, sens_dat

# funtion to get choice from a list
def txtmenu(tit_str,opt_lst):
    # funtion to get choice from a list
    print('\n'+tit_str+':')
    print('~'*len(tit_str))
    v_chs  = set(range(1,len(opt_lst)+1))
    for i_opts in range(len(opt_lst)):
        print(" "+str(i_opts+1)+") "+opt_lst[i_opts])
    inp = input("? ")
    inp_invalid = True
    while inp_invalid:
        try:
            ans = int(inp)
            if ans not in v_chs:
                raise Exception('not valid choice, try again')
            inp_invalid = False
        except ValueError:
            print("Input should be a number, try again")
            inp = input("? ")
        except Exception as err:
            print(err)
            inp = input("? ")

    return ans-1

# function that returns a list of directories
def listdirs(strt_dir):
    # function that returns a list of directories
    dir_lst = []
    for entry in os.scandir(strt_dir):
        if entry.is_dir():
            dir_lst.append(entry.name)
    return dir_lst

# function to take list of previous session names and a default name for new
# session and return users choice of new session name
def get_sessionname(prev_lst,def_name):
    # function to take list of previous session names and a default name for new
    # session and return users choice of new session name
    # requires:
    # from tkinter import *
    # from tkinter import font
    # INITIALISE parameters
    # background colour
    bcol = 'linen'
    # font size
    f_sz = 11
    # base height (px)
    b_hgt = 182
    # height of listbox in lines
    lst_hgt = max(1,len(prev_lst))
    # window size
    w_hgt = round(b_hgt + f_sz*4/3*lst_hgt)
    # window title
    wnd_tit = 'Name new session'
    # FUNCTION definitions
    # function to read entry box when ok button clicked and exit
    def click_ok():
        s_name = ent.get()
        usr_chose.set(True)
        root.destroy()
    # function to read entry box when return pressed and exit
    def name_ent(event):
        s_name = ent.get()
        usr_chose.set(True)
        root.destroy()
    # function to read double-clicked line in listbox and write into entrybox
    def old2new(event):
        # get selected item from list
        sel_item = prev_lst[lbox.curselection()[0]]
        # write it to entry box
        s_name.set(sel_item)
    def val_entry():
        return False
    # CREATE window
    # create root
    root = Tk()
    # flag to indicate choice has been made (i.e. window not closed). Must use
    # tkinter varables as can't use python global vars. These must be created after 'root = Tk()'
    usr_chose = BooleanVar()
    usr_chose.set(False)
    # set title of dialogue
    root.title(wnd_tit)
    # set height of window
    root.geometry('260x{}'.format(w_hgt))
    # set font size for widgets
    customFont = font.Font(size=f_sz)
    # create listbox
    lbox = Listbox(root, height=lst_hgt, font=customFont, bg=bcol)
    # populate listbox
    cnt = 1
    for i_lst in prev_lst:
        lbox.insert(cnt,i_lst)
        cnt += 1
    # bind listbox to return keypress to call old2new
    lbox.bind("<Return>",old2new)
    # bind listbox to double click to call old2new
    lbox.bind("<Double-Button-1>",old2new)
    # label for listbox
    lbox_lab = Label(root, text = 'Previous sessions', font=customFont)
    # create string var for entry box with default name
    s_name = StringVar()
    s_name.set(def_name)
    # Entry box to get name of session
    # TO DO validate entry here
    ent = Entry(root, font=customFont, textvariable=s_name, bg=bcol)
    # set focus to entry box
    ent.focus_set()
    # bind entry box widget to return keypress
    ent.bind("<Return>",name_ent)
    # label for entry box
    ebox_lab = Label(root, text = 'New session', font=customFont)
    # ok button to record entry
    butt = Button(root, font=customFont, text = 'OK', command=click_ok)
    # assemble widgets
    lbox_lab.pack(pady=(5,0))
    lbox.pack(padx=(15))
    ebox_lab.pack(pady=(25,0))
    ent.pack(padx=(15))
    butt.pack(pady=(20,0))
    root.mainloop()
    # if user doesn't close window return what's in entry box
    if usr_chose.get():
        return(s_name.get())
    else:
        return(None)
