#! python3

# PostRipProcess.py - script run by dBpoweramp CD Ripper after a CD has
# been ripped.
#
# * Rename the .CUE file to use the album title
# * Run the CheckFlacTags script to look for metadata problems.

# This script needs to know where the album was ripped after the rip process
# completes.  Since this script is run as an 'After Batch' script in CD Ripper,
# no dynamic arguments can be passed into the script.  To work around that,
# another script, LogRippedTrack.py, is run as an 'After Conversion' script
# so it runs after every track is ripped.  That script can be passed dynamic
# arguments, so it is given the desired CUE file name and the folder where the
# ripped album was stored.  LogRippedTrack.py can then write those two items
# where this script can find them.

# To handle multiple instances of CD Ripper being run in parallel, the script
# LogRippedTrack.py must write its output in a file whose name depends on
# the CD Ripper instance.  This script must then read from that same file.
# The file is named %TEMP%\LastRipped-PID.txt, where PID is replaced with the
# process ID of the CD Ripper instance, found by following up the chain of
# parent PIDs until we find 'CDGrab.exe'.
#
# One more complication - this script needs to run in a visible console window,
# and it shouldn't hold up the CD Ripper process.  To enable that, we actually
# run this script twice.  CD Ripper will invoke this script with no arguments,
# in a cmd.exe instance without a console window.  The absence of arguments
# tells the script to find the CD Ripper PID, and then to reinvoke itself with
# the PID as an argument.  The reinvoking is via "start", which will give the
# script a visible console window in which to run, and which runs disassociated
# from CD Ripper, which can then proceed.

import os
import psutil
import re
import sys
import tempfile

max_pathlen = 259

if len(sys.argv) == 1:
    # No arguments, so this is the first invocation.  Find the CD Ripper
    # process ID and reinvoke with that as the argument.
    pid = os.getpid()
    try:
        while True:
            proc = psutil.Process(pid)
            if proc.name().lower() == 'cdgrab.exe':
                arg = str(proc.pid)
                break
            pid = proc.ppid()
    except Exception as e:
        # Couldn't find parent CD Ripper process.  Reinvoke with a code
        # indicating the error.
        print(e)
        arg = 'FAIL'
    cmd = 'start python3 "%s" %s' % (sys.argv[0], arg)
    os.system(cmd)
    sys.exit(int(arg == 'FAIL'))

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    # Work around UnicodeEncodeErrors when attempting to print to the Windows
    # console using a non-unicode code page.  Replacement for print().
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

class Error(Exception):
    # We need the equivalent of a DOS 'pause' before exiting the script, so
    # use a private exception whenever we need to exit early.
    pass

try:
    uprint('')

    if sys.argv[1] == 'FAIL':
        raise Error("Can't find CD Ripper process, aborting script")

    # LogRippedTrack leaves its output in %TEMP%\LastRipped-PID.txt, where
    # PID is passed into the script.
    infile = 'LastRipped-%s.txt' % sys.argv[1]
    infile_path = os.path.join(tempfile.gettempdir(), infile)

    # Read the two lines that LogRippedTrack output.  First line is the name of
    # the cuesheet file to create, second line is the album directory.  Both lines
    # might be double-quote protected, possibly with spaces around those quotes.
    try:
        with open(infile_path, 'rt', encoding='UTF-8') as file:
            def clean(line):
                line = re.sub(r'^ *"?', '', line)
                line = re.sub(r'"? *[\r\n]+$', '', line)
                return line
            cue, folder = [clean(next(file)) for _ in range(2)]
    except FileNotFoundError:
        raise Error("Could not find %%TEMP%%\%s - are you missing the Run "
                       "External DSP to execute LogRippedTrack.py?" % infile)
    except StopIteration:
        raise Error("Could not read two lines from %%TEMP%%\%s - "
                       "file malformed?" % infile)

    # The cuesheet filename may have reserved characters in it.  Perform the same
    # translation that dBpoweramp performs on filenames.
    xlat_in = r'"<>?:\/*|'
    xlat_out = "'\u00bb\u00ab\u00bf;----"
    cue = cue.translate(str.maketrans(xlat_in, xlat_out))

    # Get rid of any trailing path separator on the album folder
    folder = folder.rstrip(r"\/")

    old_cue_file = os.path.join(folder, 'cuesheet.cue')
    new_cue_file = os.path.join(folder, cue)
    if not os.path.isfile(old_cue_file):
        uprint("Can't find 'cuesheet.cue' to rename")
    else:
        if len(new_cue_file) > max_pathlen:
            # cuesheet.cue exists, so we know the path isn't too long, and it's
            # safe to truncate the full pathname.
            base, ext = os.path.splitext(new_cue_file)
            new_cue_file = base[:max_pathlen - len(new_cue_file)].rstrip() + ext
            uprint("Warning: truncating the name of the new cuesheet")
        uprint("Renaming 'cuesheet.cue' to '%s'" % os.path.basename(new_cue_file))
        os.rename(old_cue_file, new_cue_file)

    os.system('CheckFlacTags.py -Sv "%s"' % folder)
except Error as e:
    uprint(e)
    exit_code = 1
except Exception as e:
    uprint(e)
    exit_code = 2
else:
    exit_code = 0

try:
    input('\nPress Enter when ready...')
except:
    pass

sys.exit(exit_code)
