import os
import sys

from subprocess import PIPE, Popen

from crossfiledialog import strings
from crossfiledialog.exceptions import FileDialogException


class KDialogException(FileDialogException):
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


def run_kdialog(*args, **kwargs):
    cmdlist = ['kdialog']
    cmdlist.extend('--{0}'.format(arg) for arg in args)

    if "start_dir" in kwargs:
        cmdlist.append(kwargs.pop("start_dir"))

    if "filter" in kwargs:
        cmdlist.append(kwargs.pop("filter"))

    for k, v in kwargs.items():
        cmdlist.append('--{0}'.format(k))
        cmdlist.append(v)

    extra_kwargs = dict()
    preferred_cwd = get_preferred_cwd()
    if preferred_cwd:
        extra_kwargs['cwd'] = preferred_cwd

    process = Popen(cmdlist, stdout=PIPE, stderr=PIPE, **extra_kwargs)
    stdout, stderr = process.communicate()

    if process.returncode == -1:
        raise KDialogException("Unexpected error during kdialog call")

    stdout, stderr = stdout.decode(), stderr.decode()
    if stderr.strip():
        sys.stderr.write(stderr)

    return stdout.strip()


def open_file(title=strings.open_file, start_dir=None, filter=None):
    kdialog_kwargs = dict(title=title)

    if start_dir:
        kdialog_kwargs["start_dir"] = start_dir

    if filter:
        if isinstance(filter, str):
            # filter is a single wildcard
            kdialog_kwargs["filter"] = filter
        elif isinstance(filter, list):
            if isinstance(filter[0], str):
                # filter is a list of wildcards
                kdialog_kwargs["filter"] = " ".join(filter)
            elif isinstance(filter[0], list):
                # filter is a list of list with wildcards
                kdialog_kwargs["filter"] = " | ".join(
                    " ".join(f) for f in filter
                )
            else:
                raise ValueError("Invalid filter")
        elif isinstance(filter, dict):
            # filter is a dictionary mapping descriptions to wildcards or lists of wildcards
            filters = []
            for key, value in filter.items():
                if isinstance(value, str):
                    filters.append(f"{key} ({value})")
                elif isinstance(value, list):
                    filters.append(f"{key} ({' '.join(value)})")
                else:
                    raise ValueError("Invalid filter")

            kdialog_kwargs["filter"] = " | ".join(
                filters
            )
        else:
            raise ValueError("Invalid filter")

    result = run_kdialog('getopenfilename', **kdialog_kwargs)
    if result:
        set_last_cwd(result)
    return result


def open_multiple(title=strings.open_multiple, start_dir=None):
    kdialog_kwargs = dict(title=title)

    if start_dir:
        kdialog_kwargs["start_dir"] = start_dir

    if filter:
        if isinstance(filter, str):
            # filter is a single wildcard
            kdialog_kwargs["filter"] = filter
        elif isinstance(filter, list):
            if isinstance(filter[0], str):
                # filter is a list of wildcards
                kdialog_kwargs["filter"] = " ".join(filter)
            elif isinstance(filter[0], list):
                # filter is a list of list with wildcards
                kdialog_kwargs["filter"] = " | ".join(
                    " ".join(f) for f in filter
                )
            else:
                raise ValueError("Invalid filter")
        elif isinstance(filter, dict):
            # filter is a dictionary mapping descriptions to wildcards or lists of wildcards
            filters = []
            for key, value in filter.items():
                if isinstance(value, str):
                    filters.append(f"{key} ({value})")
                elif isinstance(value, list):
                    filters.append(f"{key} ({' '.join(value)})")
                else:
                    raise ValueError("Invalid filter")

            kdialog_kwargs["filter"] = " | ".join(
                filters
            )
        else:
            raise ValueError("Invalid filter")

    result = run_kdialog('getopenfilename', 'multiple', **kdialog_kwargs)
    result_list = list(map(str.strip, result.split(' ')))
    if result_list:
        set_last_cwd(result_list[0])
        return result_list
    return []


def save_file(title=strings.save_file, start_dir=None):
    kdialog_args = ['getsavefilename']
    kdialog_kwargs = dict(title=title)

    if start_dir:
        kdialog_kwargs["start_dir"] = start_dir

    result = run_kdialog(*kdialog_args, **kdialog_kwargs)
    if result:
        set_last_cwd(result)
    return result


def choose_folder(title=strings.choose_folder, start_dir=None):
    kdialog_kwargs = dict(title=title)

    if start_dir:
        kdialog_kwargs["start_dir"] = start_dir

    result = run_kdialog('getexistingdirectory', **kdialog_kwargs)
    if result:
        set_last_cwd(result)
    return result


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']
