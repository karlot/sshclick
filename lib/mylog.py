# TODO: Deprecate this
from ssh_globals import *

def debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def info(msg):
    print(f"[INFO] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")

