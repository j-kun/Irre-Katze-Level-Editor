import platform
import sys

osName = platform.system().lower()

def isMac():
    return osName == "darwin"

def isLinux():
    return osName == "linux"

def isWindows():
    return osName == "windows"


def isPython2():
    return sys.version_info[0] < 3

def isPython3():
    return not isPython2()


if __name__=='__main__':
    print("isMac    : {0}".format(isMac()))
    print("isLinux  : {0}".format(isLinux()))
    print("isWindows: {0}".format(isWindows()))
