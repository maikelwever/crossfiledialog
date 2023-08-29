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
    """
    Open a file selection dialog for selecting a file using Zenity.

    Args:
        title (str, optional): The title of the file selection dialog.
            Default is 'Choose a file'
        start_dir (str, optional): The starting directory for the dialog.
        filter (str, list, dict, optional): The filter for file types to display.

    Returns:
        str: The selected file's path.

    Example:
        result = open_file(title="Select a file", start_dir="/path/to/starting/directory", filter="*.txt")
    """
    zenity_args = []
    zenity_kwargs = dict(title=title)

    if start_dir:
        # If the path doesn't end with a backslash, Zenity only
        # starts in the parent directory and selects the directory.
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    if filter:
        if isinstance(filter, str):
            # Filter is a single wildcard.
            zenity_kwargs["file-filter"] = filter
        elif isinstance(filter, list):
            # Filter is a list of wildcards.
            if isinstance(filter[0], str):
                zenity_kwargs["file-filter"] = " ".join(filter)
            elif isinstance(filter[0], list):
                zenity_args.extend("file-filter={0}".format(' '.join(f)) for f in filter)
        elif isinstance(filter, dict):
            # Filter is a dictionary mapping descriptions to wildcards.
            for key, value in filter.items():
                if isinstance(value, str):
                    zenity_args.append("file-filter={0} | {1}".format(key, value))
                elif isinstance(value, list):
                    zenity_args.append("file-filter={0} | {1}".format(key, ' | '.join(value)))
                else:
                    raise ValueError("Invalid filter")
        else:
            raise ValueError("Invalid filter")

    result = run_zenity('file-selection', *zenity_args, **zenity_kwargs)
    if result:
        set_last_cwd(result)
    return result


def open_multiple(title=strings.open_multiple, start_dir=None, filter=None):
    """
    Open a file selection dialog for selecting multiple files using Zenity.

    Args:
        title (str, optional): The title of the file selection dialog.
            Default is 'Choose one or more files'
        start_dir (str, optional): The starting directory for the dialog.
        filter (str, list, dict, optional): The filter for file types to display.

    Returns:
        list[str]: A list of selected file paths.

    Example:
        result = open_multiple(title="Select multiple files",
        start_dir="/path/to/starting/directory", filter="*.txt")
    """
    zenity_args = []
    zenity_kwargs = dict(title=title)

    if start_dir:
        # If the path doesn't end with a backslash, Zenity only starts in the parent directory
        # and selects the directory in the dialog.
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    if filter:
        if isinstance(filter, str):
            # Filter is a single wildcard.
            zenity_kwargs["file-filter"] = filter
        elif isinstance(filter, list):
            # Filter is a list of wildcards.
            if isinstance(filter[0], str):
                zenity_kwargs["file-filter"] = " ".join(filter)
            elif isinstance(filter[0], list):
                zenity_args.extend("file-filter={0}".format(' '.join(f)) for f in filter)
        elif isinstance(filter, dict):
            # Filter is a dictionary mapping descriptions to wildcards.
            for key, value in filter.items():
                if isinstance(value, str):
                    zenity_args.append("file-filter={0} | {1}".format(key, value))
                elif isinstance(value, list):
                    zenity_args.append("file-filter={0} | {1}".format(key, ' | '.join(value)))
                else:
                    raise ValueError("Invalid filter")
        else:
            raise ValueError("Invalid filter")

    result = run_zenity('file-selection', 'multiple', *zenity_args, **zenity_kwargs)
    split_result = result.split('|')
    if split_result:
        set_last_cwd(split_result[0])
        return split_result
    return []


def save_file(title=strings.save_file, start_dir=None):
    """
    Open a save file dialog using Zenity.

    Args:
        title (str, optional): The title of the save file dialog.
            Default is 'Enter the name of the file to save to'
        start_dir (str, optional): The starting directory for the dialog.

    Returns:
        str: The selected file's path for saving.

    Example:
        result = save_file(title="Save file", start_dir="/path/to/starting/directory")
    """
    zenity_args = ['file-selection', 'save', 'confirm-overwrite']
    zenity_kwargs = dict(title=title)

    if start_dir:
        # If the path doesn't end with a backslash, Zenity only starts in the parent directory
        # and selects the directory in the dialog.
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    result = run_zenity(*zenity_args, **zenity_kwargs)
    if result:
        set_last_cwd(result)
    return result


def choose_folder(title=strings.choose_folder, start_dir=None):
    """
    Open a folder selection dialog using Zenity.

    Args:
        title (str, optional): The title of the folder selection dialog.
            Default is 'Choose a folder'
        start_dir (str, optional): The starting directory for the dialog.

    Returns:
        str: The selected folder's path.

    Example:
        result = choose_folder(title="Select folder", start_dir="/path/to/starting/directory")
    """
    zenity_kwargs = dict(title=title)

    if start_dir:
        # If the path doesn't end with a backslash, Zenity only starts in the parent directory
        # and selects the directory in the dialog.
        if start_dir[-1] != "/":
            start_dir += "/"
        zenity_kwargs["filename"] = start_dir

    result = run_zenity('file-selection', 'directory', **zenity_kwargs)
    if result:
        set_last_cwd(result)
    return result


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']
