#! python3

# Script run by dBpoweramp CD Ripper after each track has been ripped.
#
# CD Ripper allows dynamic naming expansion (e.g. [artist] replaced by the
# artist name) in arguments passed to external scripts, but only for the
# before and after conversion operations, which in CD Ripper means after
# each track.  So for each track, this script is called, passing the name
# of the eventual CUE file, and the destination folder of the rip.
#
# Log those two arguments so the post-rip script, PostRipProcess.py, can
# retrieve the data.  The arguments should be passed in surrounded by double
# quotes.

# To handle multiple instances of CD Ripper being run in parallel, the args
# are saved in a file whose name depends on the CD Ripper instance.  This
# script will determine the process ID (PID) of the CD Ripper instance, then
# use that in the file name.

import os
import psutil
import sys
import tempfile

pid = os.getpid()
try:
    while True:
        proc = psutil.Process(pid)
        if proc.name().lower() == 'cdgrab.exe':
            break
        pid = proc.ppid()
except:
    print('Script not run from within CD Ripper, aborting')
    sys.exit(1)

fname = os.path.join(tempfile.gettempdir(), 'LastRipped-%d.txt' % pid)
with open(fname, 'wt', encoding='UTF-8') as f:
    print(sys.argv[1], file=f)
    print(sys.argv[2], file=f)
