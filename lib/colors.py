# TODO: Deprecate this...
class bcolors:
    #---------------------
    RESET   = '\033[0m'
    BRIGHT  = '\033[1m'
    DIM     = '\033[2m'
    NORMAL  = '\033[22m'
    #---------------------
    BLACK   = '\033[30m'
    RED     = '\033[31m'
    GREEN   = '\033[32m'
    YELLOW  = '\033[33m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    WHITE   = '\033[37m'


def red(msg):
    return bcolors.RED + msg + bcolors.RESET
def green(msg):
    return bcolors.GREEN + msg + bcolors.RESET
def yellow(msg):
    return bcolors.YELLOW + msg + bcolors.RESET
def blue(msg):
    return bcolors.BLUE + msg + bcolors.RESET
def magenta(msg):
    return bcolors.MAGENTA + msg + bcolors.RESET
def cyan(msg):
    return bcolors.CYAN + msg + bcolors.RESET

def bred(msg):
    return bcolors.BRIGHT + bcolors.RED + msg + bcolors.RESET
def bgreen(msg):
    return bcolors.BRIGHT + bcolors.GREEN + msg + bcolors.RESET
def byellow(msg):
    return bcolors.BRIGHT + bcolors.YELLOW + msg + bcolors.RESET
def bblue(msg):
    return bcolors.BRIGHT + bcolors.BLUE + msg + bcolors.RESET
def bmagenta(msg):
    return bcolors.BRIGHT + bcolors.MAGENTA + msg + bcolors.RESET
def bcyan(msg):
    return bcolors.BRIGHT + bcolors.CYAN + msg + bcolors.RESET
