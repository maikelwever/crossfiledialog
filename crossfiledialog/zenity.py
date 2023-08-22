import os
import sys

from subprocess import PIPE, Popen

from crossfiledialog import strings
from crossfiledialog.exceptions import FileDialogException


class ZenityException(FileDialogException):
    pass


last_cwd = None


def get_preferred_cwd():
    possible_cwd = os.environ.get('FILEDIALOG_CWD', '')
    if possible_cwd:
        return possible_cwd

    global last_cwd
    if last_cwd:
        return last_cwd


def set_last_cwd(cwd):
    global last_cwd
    last_cwd = os.path.dirname(cwd)


def run_zenity(*args, **kwargs):
    cmdlist = ['zenity']
    cmdlist.extend('--{0}'.format(arg) for arg in args)
    cmdlist.extend('--{0}={1}'.format(k, v) for k, v in kwargs.items())

    extra_kwargs = dict()
    preferred_cwd = get_preferred_cwd()
    if preferred_cwd:
        extra_kwargs['cwd'] = preferred_cwd

    process = Popen(cmdlist, stdout=PIPE, stderr=PIPE, **extra_kwargs)
    stdout, stderr = process.communicate()

    if process.returncode == -1:
        raise ZenityException("Unexpected error during zenity call")

    stdout, stderr = stdout.decode(), stderr.decode()

    if stderr.strip():
        sys.stderr.write(stderr)

    return stdout.strip()


def open_file(title=strings.open_file, start_dir=None, filter=None):
    zenity_kwargs = dict(title=title)
    
    if start_dir:
        # if path doesnt end with a backslash, zenity only starts in the parent directory 
        # and selects the directory in the dialog
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    if filter:
        pass

    result = run_zenity('file-selection', **zenity_kwargs)
    if result:
        set_last_cwd(result)
    return result


def open_multiple(title=strings.open_multiple, start_dir=None):
    zenity_kwargs = dict(title=title)

    if start_dir:
        # if path doesnt end with a backslash, zenity only starts in the parent directory 
        # and selects the directory in the dialog
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    if filter:
        pass

    result = run_zenity('file-selection', 'multiple', **zenity_kwargs)
    split_result = result.split('|')
    if split_result:
        set_last_cwd(split_result[0])
        return split_result
    return []


def save_file(title=strings.save_file, start_dir=None):
    zenity_args = ['file-selection', 'save', 'confirm-overwrite']
    zenity_kwargs = dict(title=title)

    if start_dir:
        # if path doesnt end with a backslash, zenity only starts in the parent directory 
        # and selects the directory in the dialog
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    result = run_zenity(*zenity_args, **zenity_kwargs)
    if result:
        set_last_cwd(result)
    return result


def choose_folder(title=strings.choose_folder, start_dir=None):
    zenity_kwargs = dict(title=title)

    if start_dir:
        # if path doesnt end with a backslash, zenity only starts in the parent directory 
        # and selects the directory in the dialog
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    result = run_zenity('file-selection', 'directory', **zenity_kwargs)
    if result:
        set_last_cwd(result)
    return result


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']

