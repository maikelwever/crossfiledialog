import os
import sys

from crossfiledialog.exceptions import NoImplementationFoundException


def which(command):
    for d in os.environ['PATH'].split(':'):
        if os.path.exists(d):
            for binary in os.listdir(d):
                if binary == command:
                    return os.path.join(d, command)


if sys.platform == 'linux':
    probably_kde = os.environ.get('DESKTOP_SESSION', '').lower() == 'kde' or \
            os.environ.get('XDG_CURRENT_DESKTOP', '').lower() == 'kde'

    kdialog_binary = which('kdialog')
    zenity_binary = which('zenity')

    if kdialog_binary and (probably_kde or not zenity_binary):
        from crossfiledialog.kdialog import *
    elif zenity_binary:
        from crossfiledialog.zenity import *
    else:
        raise NoImplementationFoundException()

elif sys.platform == 'win32':
    from crossfiledialog.win32 import *

else:
    raise NoImplementationFoundException()


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']

