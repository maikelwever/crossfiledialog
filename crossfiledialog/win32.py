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


def open_file(title=strings.open_file, filter=None):
    file_name = error_handling_wrapper(
        win32gui.GetOpenFileNameW,
        Title=title
    )

    if file_name:
        set_last_cwd(file_name)
    return file_name


def open_multiple(title=strings.open_multiple):
    file_names = error_handling_wrapper(
        win32gui.GetOpenFileNameW,
        Title=title,
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


def save_file(title=strings.save_file):
    file_name = error_handling_wrapper(
        win32gui.GetSaveFileNameW,
        Title=title,
        Flags=win32con.OFN_OVERWRITEPROMPT,
    )

    if file_name:
        set_last_cwd(file_name)
    return file_name


def choose_folder(title=strings.choose_folder):
    desktop_pidl = shell.SHGetFolderLocation(0, shellcon.CSIDL_DESKTOP, 0, 0)
    pidl, display_name, image_list = shell.SHBrowseForFolder(
        win32gui.GetDesktopWindow(), desktop_pidl,
        title, 0, None, None
    )

    if pidl:
        path = shell.SHGetPathFromIDListW(pidl)
        set_last_cwd(path)
        return path


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']
