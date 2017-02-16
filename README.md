# wiicop.py

Python 3 software for obtaining centre of pressure data from the Nintendo Wii board. Works on linux computers only. Also obtains subject code and experiment factors such as group (case/control), acquisition time etc. This is used by students and researchers at the British School of Osteopathy, London [website](http://www.bso.ac.uk/).

#HOW TO USE
1. Follow all the install instructions below

2. Via a terminal, cd to the wiicp.py directory and run wiicop.py:
    `./wiicop.py`
    
3. You then calibrate the board for that session. Apply calibration weights, as accurately as possible, to the centre of the board. You can configure which weights to use by editing the top of 'wiicop.py'. The weight options are defined in a dictionary `pd.Series`, numbered from 0. Choose also the units.

    `# Pandas series to define calibration weights`
    
    `calib_wgts = pd.Series({0:5,1:9,2:16.5})`
    
    `# calibration units ('Kgs' or 'lbs')`
    
    `calib_units = 'Kgs'`
    
    The calibration will check that all the sensors are obtaining 95% of readings that are greater than zero. If insufficiently heavy calibration weights are used, or the surface is uneven, one of the sensors will be floating in the air and not taking readings. The program will terminate if that is the case. The program fits a linear model to the data from each sensor and saves the details in the session directory. 

4. If set up correctly, it should ask via the command line to choose a study. Then you create a name for the session. A name will be suggested but check one hasn't already got the same name (i.e. if you've done another session the same morning)

5. You will then be able to choose study factors for the study. E.g. 'before' or 'after', 'treatment' or 'control' etc.

6. A window will then pop up displaying the centre of pressure as a green dot. To start recording data, press the spacebar. If you have configured it to do a timed acquisition, it will stop after the time is up. Otherwise you can stop the acquisition by pressing the spacebar again.

7. You will be asked if you want to get another aquisition. If you choose no, the session will terminate.

8. You can use `GetCOPparams.py` to read the COP and the calibration data. Currently it calculates area of 95% prediction ellipse (thanks to Marcos Duarte for `hyperellipsoid.py`. https://github.com/demotu/BMC), path length and path velocity.



#INSTALL INSTRUCTIONS


1. Go to [here](https://github.com/dvdhrm/xwiimote) to download the zip file containing the xwiimote software and unzip it in a suitable directory. Or clone using git.

2. Go to [here](https://github.com/dvdhrm/xwiimote-bindings) to download the zip file containing the xwiimote bindings and unzip it another directory. Or clone using git.

3. Install the following dependencies (ubuntu based distributions) via:

    `sudo apt-get install libudev-dev libncurses5-dev libncursesw5-dev autoconf autogen libtool swig python3-dev python3-tk python3-pip`

4. Install python modules:

    `sudo pip3 install pyudev pandas matplotlib`

5. Compile and install xwiimote library.
Change (cd) to xwiimote directory (xwiimote-master), then run:

    `sudo ./autogen.sh`
    
    `sudo ./configure`
    
    `sudo make`
    
    `sudo make install`
    

6. Create the xwiimote configure file in /etc/ld.so.comf.d:

    `cd /etc/ld.so.conf.d`
    
    `sudo nano xwiimote.conf`

    And add the following line to this file:

    `/usr/local/lib`

    and save: Ctrl O, Ctrl X. Next, reload library cache using the following:

    `sudo ldconfig`

7. Test xwiimote libraries are installed and can connect Wiiboard by connecting Wiiboard via Bluetooth and running:

    `sudo xwiishow`

    and follow instructions.

8. Compile and install xwiimote python bindings. Change (cd) to xwiimote-bindings directory and run following:

    `sudo ./autogen.sh`
    
    `sudo ./configure PYTHON=/usr/bin/python3`
    
    `sudo make`
    
    `sudo make install`
    

9. Add user to input group to allow user (‘usersname’) to run xwiimote software:

    `sudo usermod -a -G input usersname`

    then log out and log back in again

10. Create a directory to put the wiiboard software into, e.g. ~/Wiiboard. Copy wiicop.py and WiiCopFunctions.py into this directory. Then add this directory to your python path by adding this line to your ~/.bashrc file:

    `export PYTHONPATH="$PYTHONPATH:home/yourusername/path/to/wiicopdir"`

11. In same directory create a directory called config_files to put study configuration files for each study. These need to be amended – see below.

12. Make sure the python file 'wiicop.py' is executable.

    Either: Right click on it, select 'Properties', select 'Permissions' tab and tick the 'Allow executing file as program' tickbox.

    Or: In a terminal, cd to directory of wiicop.py and run:

    `chmod +x wiicop.py`

12. Create a study directory and a sub directory for each study. Amend config file for each study to point to the right directory


#NOTES:
    In Linux Mint 18 Cinnamon edition the default bluetooth (Blueberry) tool doesn't seem to work. Uninstalling it and installing Blueman seems to work:
    
    sudo apt-get remove --purge blueberry
    sudo apt-get install blueman
    
Then reboot
    




