import sys

from subprocess import PIPE, Popen

from filedialog.exceptions import FileDialogException


class KDialogException(FileDialogException):
    pass


def run_kdialog(*args, **kwargs):
    cmdlist = ['kdialog']
    cmdlist.extend('--{0}'.format(arg) for arg in args)
    for k, v in kwargs.items():
        cmdlist.append('--{0}'.format(k))
        cmdlist.append(v)

    process = Popen(cmdlist, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == -1:
        raise KDialogException("Unexpected error during kdialog call")

    stdout, stderr = stdout.decode(), stderr.decode()
    if stderr.strip():
        sys.stderr.write(stderr)

    return stdout.strip()


def open_file(title='Choose a file', filter=None):
    kdialog_kwargs = dict(title=title)

    if filter:
        pass

    return run_kdialog('getopenfilename', **kdialog_kwargs)


def open_multiple(title='Choose one or more files'):
    kdialog_kwargs = dict(title=title)

    if filter:
        pass

    result = run_kdialog('getopenfilename', 'multiple', **kdialog_kwargs)
    return list(map(str.strip, result.split(' ')))


def save_file(title='Enter the name of the file to save to'):
    kdialog_args = ['getsavefilename']
    kdialog_kwargs = dict(title=title)
    return run_kdialog(*kdialog_args, **kdialog_kwargs)


def choose_folder(title='Choose a folder'):
    return run_kdialog('getexistingdirectory')


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']
