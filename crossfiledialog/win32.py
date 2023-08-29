import os

from crossfiledialog import strings
from crossfiledialog.exceptions import NoImplementationFoundException, FileDialogException

try:
    import pywintypes
    import win32gui
    import win32con
    from win32com.shell import shell, shellcon

except ImportError:
    raise NoImplementationFoundException(
        "Running 'filedialog' on Windows requires the 'pywin32' package.")


class Win32Exception(FileDialogException):
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


def error_handling_wrapper(struct, **kwargs):
    if 'InitialDir' not in kwargs:
        kwargs['InitialDir'] = get_preferred_cwd()

    if 'Flags' in kwargs:
        kwargs['Flags'] = kwargs['Flags'] | win32con.OFN_EXPLORER
    else:
        kwargs['Flags'] = win32con.OFN_EXPLORER

    try:
        file_name, custom_filter, flags = struct(**kwargs)
        return file_name

    except pywintypes.error:
        return None


def open_file(title=strings.open_file, start_dir=None, filter=None):
    """
    Open a file selection dialog for selecting a file using the Windows API.

    Args:
        title (str, optional): The title of the file selection dialog.
            Default is 'Choose a file'
        start_dir (str, optional): The starting directory for the dialog.
        filter (str, list, dict, optional): The filter for file types to display.

    Returns:
        str: The selected file's path.

    Example:
        result = open_file(title="Select a file", start_dir="C:/Documents", filter="*.txt")
    """
    win_kwargs = dict(Title=title)

    if start_dir:
        win_kwargs["InitialDir"] = start_dir

    if filter:
        if isinstance(filter, str):
            # Filter is a single wildcard.
            win_kwargs["Filter"] = filter + '\0' + filter + '\0'
        elif isinstance(filter, list):
            if isinstance(filter[0], str):
                # Filter is a list of wildcards.
                win_kwargs["Filter"] = " ".join(filter) + '\0' + ";".join(filter) + '\0'
            elif isinstance(filter[0], list):
                # Filter is a list of list with wildcards.
                win_kwargs["Filter"] = "".join(
                    " ".join(f) + '\0' + ";".join(f) + '\0' for f in filter
                )
            else:
                raise ValueError("Invalid filter")
        elif isinstance(filter, dict):
            # Filter is a dictionary mapping descriptions to wildcards or lists of wildcards.
            filters = ""
            for key, value in filter.items():
                if isinstance(value, str):
                    filters += "{0}\0{1}\0".format(key, value)
                elif isinstance(value, list):
                    filters += "{0}\0{1}\0".format(key, ';'.join(value))
                else:
                    raise ValueError("Invalid filter")

            win_kwargs["Filter"] = filters
        else:
            raise ValueError("Invalid filter")

    file_name = error_handling_wrapper(
        win32gui.GetOpenFileNameW,
        **win_kwargs
    )

    if file_name:
        set_last_cwd(file_name)
    return file_name


def open_multiple(title=strings.open_multiple, start_dir=None, filter=None):
    """
    Open a file selection dialog for selecting multiple files using the Windows API.

    Args:
        title (str, optional): The title of the file selection dialog.
            Default is 'Choose one or more files'
        start_dir (str, optional): The starting directory for the dialog.
        filter (str, list, dict, optional): The filter for file types to display.

    Returns:
        list[str]: A list of selected file paths.

    Example:
        result = open_multiple(title="Select multiple files", start_dir="C:/Documents", filter="*.txt")
    """
    win_kwargs = dict(Title=title)

    if start_dir:
        win_kwargs["InitialDir"] = start_dir

    if filter:
        if isinstance(filter, str):
            # Filter is a single wildcard.
            win_kwargs["Filter"] = filter + '\0' + filter + '\0'
        elif isinstance(filter, list):
            if isinstance(filter[0], str):
                # Filter is a list of wildcards.
                win_kwargs["Filter"] = " ".join(filter) + '\0' + ";".join(filter) + '\0'
            elif isinstance(filter[0], list):
                # Filter is a list of list with wildcards.
                win_kwargs["Filter"] = "".join(
                    " ".join(f) + '\0' + ";".join(f) + '\0' for f in filter
                )
            else:
                raise ValueError("Invalid filter")
        elif isinstance(filter, dict):
            # Filter is a dictionary mapping descriptions to wildcards or lists of wildcards.
            filters = ""
            for key, value in filter.items():
                if isinstance(value, str):
                    filters += "{0}\0{1}\0".format(key, value)
                elif isinstance(value, list):
                    filters += "{0}\0{1}\0".format(key, ';'.join(value))
                else:
                    raise ValueError("Invalid filter")

            win_kwargs["Filter"] = filters
        else:
            raise ValueError("Invalid filter")

    file_names = error_handling_wrapper(
        win32gui.GetOpenFileNameW,
        **win_kwargs,
        Flags=win32con.OFN_ALLOWMULTISELECT,
    )

    if file_names:
        file_names_list = file_names.split('\x00')
        if len(file_names_list) > 1:
            dirname = file_names_list[0]
            file_names_list_nodir = file_names_list[1:]
            file_names_list = [os.path.join(dirname, file_name) for file_name in file_names_list_nodir]

        set_last_cwd(file_names_list[0])
        return file_names_list

    return []


def save_file(title=strings.save_file, start_dir=None):
    """
    Open a save file dialog using the Windows API.

    Args:
        title (str, optional): The title of the save file dialog.
            Default is 'Enter the name of the file to save to'
        start_dir (str, optional): The starting directory for the dialog.

    Returns:
        str: The selected file's path for saving.

    Example:
        result = save_file(title="Save file", start_dir="C:/Documents")
    """
    win_kwargs = dict(Title=title)

    if start_dir:
        win_kwargs["InitialDir"] = start_dir

    file_name = error_handling_wrapper(
        win32gui.GetSaveFileNameW,
        **win_kwargs,
        Flags=win32con.OFN_OVERWRITEPROMPT,
    )

    if file_name:
        set_last_cwd(file_name)
    return file_name


def choose_folder(title=strings.choose_folder, start_dir=None):
    """
    Open a folder selection dialog using the Windows API.

    Args:
        title (str, optional): The title of the folder selection dialog.
            Default is 'Choose a folder'
        start_dir (str, optional): The starting directory for the dialog.

    Returns:
        str: The selected folder's path.

    Example:
        result = choose_folder(title="Choose folder", start_dir="C:/Documents")
    """
    if start_dir:
        start_pidl, _ = shell.SHParseDisplayName(start_dir, 0, None)
    elif last_cwd:
        start_pidl, _ = shell.SHParseDisplayName(last_cwd, 0, None)
    else:
        # default directory is the desktop
        start_pidl = shell.SHGetFolderLocation(0, shellcon.CSIDL_DESKTOP, 0, 0)
    pidl, display_name, image_list = shell.SHBrowseForFolder(
        win32gui.GetDesktopWindow(), start_pidl,
        title, 0, None, None
    )

    if pidl:
        path = shell.SHGetPathFromIDListW(pidl)
        set_last_cwd(path)
        return path


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']
