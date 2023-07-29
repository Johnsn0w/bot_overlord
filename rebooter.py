import time
import subprocess
import sys

print("rebooter script starting")
time.sleep(3)  # wait 3 seconds
subprocess.Popen([sys.executable, 'smiley_bot_main.py'])  # start main script

print("rebooter script exiting(I hope)")