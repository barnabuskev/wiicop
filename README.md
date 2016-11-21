# wiicop.py

Python 3 software for obtaining centre of pressure data from the Nintendo Wii board


##INSTALL INSTRUCTIONS


1. Go to [here](https://github.com/dvdhrm/xwiimote) to download the zip file containing the xwiimote software and unzip it in a suitable directory

2. Go to [here](https://github.com/dvdhrm/xwiimote-bindings) to download the zip file containing the xwiimote bindings and unzip it another directory

3. Install the following dependencies (ubuntu based distributions) via:

    sudo apt-get install libudev-dev libncurses5-dev libncursesw5-dev autoconf autogen libtool swig python-dev python3-tk python3-pip

4. Install python modules:

    pip3 install pyudev pandas matplotlib

5. Compile and install xwiimote library.
Change (cd) to xwiimote directory, then run:

    sudo ./autogen
    
    sudo ./configure
    
    sudo make
    
    sudo make install
    

6. Create the xwiimote configure file:

    cd /etc/ld.so.conf.d
    
    sudo nano xwiimote.conf

    And add the following line to this file:

    /usr/local/lib

    and save: Ctrl O, Ctrl X. Next, reload library cache using the following:

    sudo ldconfig

7. Test xwiimote libraries are installed and can connect Wiiboard by connecting Wiiboard via Bluetooth and running:

    sudo xwiishow

    and follow instructions.

8. Complile and install xwiimote python bindings. Change (cd) to xwiimote-bindings directory and run following:

    sudo ./autogen
    
    sudo ./configure PYTHON=/usr/bin/python3
    
    sudo make
    
    sudo make install
    

9. Add user to input group to allow user (‘usersname’) to run xwiimote software:

    sudo usermod -a -G input usersname

    then log out and log back in again

10. Create a directory to put the wiiboard software into, e.g. ~/Wiiboard. Copy wiicop.py and WiiCopFunctions.py into this directory. Then add this directory to your python path by adding this line to your ~/.bashrc file:

    export PYTHONPATH=$PYTHONPATH:home/yourusername/path/to/wiicopdir

11. In same directory create a directory called config_files to put study configuration files for each study. These need to be amended – see below.

12. Create a study directory and a sub directory for each study. Amend config file for each study to point to the right directory




