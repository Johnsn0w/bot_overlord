import time
import subprocess
import sys

print("rebooter script starting")
time.sleep(3)  # wait 3 seconds

print("rebooter script starting main script")
subprocess.Popen([sys.executable, 'bot_main.py']) 

print("rebooter script exiting")