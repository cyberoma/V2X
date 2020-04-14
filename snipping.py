import subprocess
import time
import os
import signal

p = subprocess.Popen(['python3', 'client_listener.py'])
print('file startet..', p)
time.sleep(10)
p.terminate()
