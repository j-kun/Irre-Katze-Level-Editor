#!/usr/bin/env python
# standard libraries
import os
import subprocess
import logging
log = logging.getLogger(__name__)

# other libraries
import system


# ---------- settings ----------

WC_FILEPATH = '{filepath}'
CMD_OPEN_FILE_WINDOWS = ("cmd", "/C", "start", "", WC_FILEPATH)
CMD_OPEN_FILE_LINUX   = ("xdg-open", WC_FILEPATH)
CMD_OPEN_FILE_MAC     = ("open", "--", WC_FILEPATH)


# ---------- internal commands ----------

def _format_open_file_cmd(cmd, filepath):
    cmd = list(cmd)
    for i in range(len(cmd)):
        cmd[i] = cmd[i].replace(WC_FILEPATH, filepath)
    return cmd

def _run_cmd(cmd):
    log.debug("executing {cmd}".format(cmd=cmd))
    return subprocess.Popen(cmd)


# ---------- interface ----------

if system.isWindows():
    def open_directory(path, select):
        '''select=True: parent directory is opened, path (file or directory) is selected.
           select=False: path (directory) is opened and nothing is selected.'''
        cmd = ["explorer"]
        if select:
            cmd.append("/select,")
        cmd.append(path)
        return _run_cmd(cmd)
    
    def open_file(path):
        cmd = _format_open_file_cmd(CMD_OPEN_FILE_WINDOWS, path)
        return _run_cmd(cmd)

elif system.isLinux():
    def open_directory(path, select):
        '''select=True: parent directory is opened, path (file or directory) is selected.
           select=False: path (directory) is opened and nothing is selected.'''
        if select:
            dirpath, filename = os.path.split(path)
        else:
            dirpath = path
        cmd = ["xdg-open", dirpath]
        return _run_cmd(cmd)
    
    def open_file(path):
        cmd = _format_open_file_cmd(CMD_OPEN_FILE_LINUX, path)
        return _run_cmd(cmd)

elif system.isMac():
    #https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/open.1.html
    def open_directory(path, select):
        '''select=True: parent directory is opened, path (file or directory) is selected.
           select=False: path (directory) is opened and nothing is selected.'''
        cmd = ["open"]
        if select:
            cmd.append("-R")
        cmd.append("--")
        cmd.append(path)
        return _run_cmd(cmd)
    
    def open_file(path):
        cmd = _format_open_file_cmd(CMD_OPEN_FILE_MAC, path)
        return _run_cmd(cmd)
        
else:
    raise ValueError("unknown operating system: "+system.osName)



# ---------- test program ----------

if __name__=='__main__':
    import os
    
    def get_some_subdirectory(path):
        l = os.listdir(path)
        for fn in l:
            ffn = os.path.join(path, fn)
            if os.path.isdir(ffn):
                if fn[0]!='.':
                    return ffn
    def get_some_file(path):
        l = os.listdir(path)
        for fn in l:
            ffn = os.path.join(path, fn)
            if os.path.isfile(ffn):
                if fn[0]!='.':
                    return ffn
        return get_some_file(get_some_subdirectory(path))

    path = os.path.expanduser("~")
    path = get_some_subdirectory(path)
    path = get_some_subdirectory(path)
    path = get_some_file(path)
    
    print(path)
    open_directory(path, select=True)
