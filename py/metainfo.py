import os
import logging
log = logging.getLogger(__name__)

"""
This library provides the information where files are located.
With the flag _stay_local you can decide whether configuration files
and log files are to be created inside of this directory (_stay_local=True)
or where they belong according to standards (_stay_local=False).

_stay_local=False has the advantages of not needing write permissions for
this directory and that different users have their own settings.

For getting the platform dependent standard paths the non-standard
library appdirs is used. It can be installed with
    pip install appdirs --user
or downloaded from
    https://pypi.python.org/pypi/appdirs/1.2.0

APP_NAME and APP_AUTHOR are required for appdirs to get the correct paths.
"""


APP_NAME   = "irrekatze-leveleditor"
APP_AUTHOR = "custom"

_stay_local = False



if not _stay_local:
    try:
        import appdirs
    except:
        _stay_local = True

_PATH_SELF   = os.path.split(__file__)[0]
_PATH_TEMPLATES = os.path.join(_PATH_SELF, "templates")
if _stay_local:
    PATH_CONFIG = os.path.join(_PATH_SELF, "config")
    PATH_LOG    = os.path.join(_PATH_SELF, "log")
else:
    PATH_CONFIG = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    PATH_LOG    = appdirs.user_log_dir(APP_NAME, APP_AUTHOR)
    

def get_config_ffn(fn, create=False, log=log):
    ffn = os.path.join(PATH_CONFIG, fn)
    if os.path.exists(ffn):
        #log.log(logging.DEBUG, "using configuration file: {ffn!r}".format(ffn=ffn))
        return ffn
    
    ffn_template = os.path.join(_PATH_TEMPLATES, fn)
    if not create:
        log.log(logging.DEBUG, "{ffn!r} does not exist. using {ffn_template!r} instead".format(ffn=ffn, ffn_template=ffn_template))
        return ffn_template

    if not os.path.isdir(PATH_CONFIG):
        log.log(logging.INFO, "creating new directory {path!r} for config file {fn!r}".format(path=PATH_CONFIG, fn=fn))
        os.makedirs(PATH_CONFIG)
    
    log.log(logging.INFO, "creating new configuration file {ffn!r} from template {ffn_template!r}".format(ffn_template=ffn_template, ffn=ffn))
    with open(ffn_template, 'rt') as f_from:
        with open(ffn, 'wt') as f_to:
            for ln in f_from:
                f_to.write(ln)
    #log.log(logging.DEBUG, "using configuration file: {ffn!r}".format(ffn=ffn))
    return ffn
