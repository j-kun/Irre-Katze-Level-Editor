#!/usr/bin/env python

# standard libraries
import os.path
import logging
log = logging.getLogger(__name__)

# other libraries
import metainfo
import open_directory


_default_filepath = metainfo.PATH_CONFIG
_default_filename = 'settings.py'
_default_ffn      = os.path.join(_default_filepath, _default_filename)

settings = dict()
#settings.get = settings.setdefault #'dict' object attribute 'get' is read-only

class KEY:
    UPDATE_SETTINGS = 'update-settings'
    _IS_SETTINGS_FILE_EXISTING = '.settings-file-is-existing'
    _IS_SETTINGS_FILE_LOADED_SUCCESSFULLY = '.settings-file-is-loaded-successfully'
    _IS_SETTINGS_FILE_OPEN = '.settings-file-is-open'
    _SETTINGS_FILE_PATH = '.settings-file-path'
    _ERROR_FAILED_TO_LOAD = '.ERROR-failed-to-load'

def load_settings(settings=settings, filename=None):
    if filename==None:
        filename = settings.get(KEY._SETTINGS_FILE_PATH, _default_ffn)
    filename = os.path.abspath(filename)
    log.info("settings file location: {fn}".format(fn=filename))
    settings.clear()
    if os.path.isfile(filename):
        try:
            with open(filename, 'rt') as f:
                code = f.read()
            env = dict()
            exec(code, env)
            saved_settings = env['settings']
            settings.update(saved_settings)
            settings[KEY._IS_SETTINGS_FILE_EXISTING] = True
            settings[KEY._IS_SETTINGS_FILE_LOADED_SUCCESSFULLY] = True
        except Exception as e:
            settings[KEY._IS_SETTINGS_FILE_EXISTING] = True
            settings[KEY._IS_SETTINGS_FILE_LOADED_SUCCESSFULLY] = False
            settings[KEY._ERROR_FAILED_TO_LOAD] = e
            log.error("failed to load settings:")
            log.exception(e)
    else:
        settings[KEY._IS_SETTINGS_FILE_EXISTING] = False
        settings[KEY._IS_SETTINGS_FILE_LOADED_SUCCESSFULLY] = False
        log.info("settings file does not exist")
    settings[KEY._SETTINGS_FILE_PATH] = filename
    settings[KEY._IS_SETTINGS_FILE_OPEN] = False

def is_settings_file_existing(settings=settings):
    return settings[KEY._IS_SETTINGS_FILE_EXISTING]

def get_fullfilename(settings=settings):
    return settings[KEY._SETTINGS_FILE_PATH]

def open_settings(settings=settings):
    #TODO: consider: what if user opens settings, closes them, performs changes on GUI and opens settings again?
    #with current implementation those changes would be lost.
    settings[KEY._IS_SETTINGS_FILE_OPEN] = True
    open_directory.open_file(os.path.abspath(settings[KEY._SETTINGS_FILE_PATH]))

def are_updates_wanted(settings=settings):
    return settings.setdefault(KEY.UPDATE_SETTINGS, False)

def save_settings(settings=settings, force=False, ask_overwrite_handler=None):
    save = False
    # settings.setdefault must go first! (otherwise I would rearrange the logic)
    if force or are_updates_wanted(settings) or not is_settings_file_existing(settings):
        if not settings[KEY._IS_SETTINGS_FILE_OPEN]:
            save = True
        elif ask_overwrite_handler!=None:
            if ask_overwrite_handler():# TODO: consider: force and 
                save = True
                settings[KEY._IS_SETTINGS_FILE_OPEN] = False
        elif force:
            log.warning("settings have been opened in external editor and ask_overwrite_handler is not given. But force is True therefore I am proceeding even at the risk of potential data loss.")
            save = True
    if save:
            log.info("saving settings")
            out = settings_to_string(settings)
            ffn = settings[KEY._SETTINGS_FILE_PATH]
            path, fn = os.path.split(ffn)
            if not os.path.isdir(path):
                log.info("creating new directory for settings file: {!r}".format(path))
                os.makedirs(path)
            with open(ffn, 'wt') as f:
                f.write(out)
            settings[KEY._IS_SETTINGS_FILE_EXISTING] = True

def settings_to_string(settings=settings, show_hidden=False):
    out = "settings = {\n"
    keys = list(settings.keys())
    keys.sort()
    for key in keys:
        if show_hidden or key[0] not in ('.', '_'):
            out += "   %r : %r,\n" % (key, settings[key])
    out += "}"
    return out
    
load_settings()
if __name__=='__main__':
    pass
