from subprocess import PIPE, Popen

from filedialog.exceptions import FileDialogException


class ZenityException(FileDialogException):
    pass


def run_zenity(*args, **kwargs):
    cmdlist = ['zenity']
    cmdlist.extend('--{0}'.format(arg) for arg in args)
    cmdlist.extend('--{0}={1}'.format(k, v) for k, v in kwargs.items())

    process = Popen(cmdlist, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == -1:
        raise ZenityException("Unexpected error during zenity call")

    if stderr.strip():
        sys.stderr.write(stderr)

    stdout, stderr = stdout.decode(), stderr.decode()
    return stdout.strip()


def open_file(title='Choose a file', filter=None):
    zenity_kwargs = dict(title=title)

    if filter:
        pass

    return run_zenity('file-selection', **zenity_kwargs)


def open_multiple(title='Choose one or more files'):
    zenity_kwargs = dict(title=title)

    if filter:
        pass

    result = run_zenity('file-selection', 'multiple', **zenity_kwargs)
    return result.split('|')


def save_file(title='Enter the name of the file to save to'):
    zenity_args = ['file-selection', 'save', 'confirm-overwrite']
    zenity_kwargs = dict(title=title)
    return run_zenity(*zenity_args, **zenity_kwargs)


def choose_folder(title='Choose a folder'):
    return run_zenity('file-selection', 'directory')


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']

