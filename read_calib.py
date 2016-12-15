#!/usr/bin/env python3
# to read a pickled file into memory
import tkinter.filedialog as tk_fd
import pickle
import numpy as np
import sys


dfile = tk_fd.askopenfilename(title = 'Get pickled data file',filetypes=[('Data files', '*.dat'),
 ('All files','*')])
if not dfile:
    print('No file chosen')
    sys.exit(0)
with open(dfile,'rb') as fptr:
    dc = pickle.load(fptr, fix_imports=False)
print(dc['details'])
