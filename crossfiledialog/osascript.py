import os
import sys

from subprocess import PIPE, Popen

from crossfiledialog import strings
from crossfiledialog.exceptions import FileDialogException


class OsascriptException(FileDialogException):
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


def run_osascript(script):
    process = Popen(['osascript', '-e', script], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise OsascriptException(f"Unexpected error during osascript call: {stderr.decode().strip()}")

    stdout, stderr = stdout.decode(), stderr.decode()

    if stderr.strip():
        sys.stderr.write(stderr)

    return stdout.strip()


def _escape_applescript_string(s):
    # Escape backslashes and double quotes for AppleScript
    return s.replace("\\", "\\\\").replace('"', '\\"')


def open_file(title=strings.open_file, start_dir=None, filter=None):
    """
    Open a file selection dialog for selecting a file using AppleScript (osascript).

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
    script = 'set chosenFile to choose file'
    if title:
        script += f' with prompt "{_escape_applescript_string(title)}"'
    if start_dir:
        script += f' default location POSIX file "{_escape_applescript_string(start_dir)}"'
    # AppleScript does not support file type filtering by wildcard, only by file type/extension
    # so we attempt to support basic extension filtering if possible
    if filter:
        file_types = []
        if isinstance(filter, str):
            if filter.startswith("*."):
                ext = filter[2:]
                file_types.append(ext)
        elif isinstance(filter, list):
            for f in filter:
                if isinstance(f, str) and f.startswith("*."):
                    file_types.append(f[2:])
        elif isinstance(filter, dict):
            for value in filter.values():
                if isinstance(value, str) and value.startswith("*."):
                    file_types.append(value[2:])
                elif isinstance(value, list):
                    for v in value:
                        if isinstance(v, str) and v.startswith("*."):
                            file_types.append(v[2:])
        if file_types:
            # AppleScript expects a list of file types as {"txt", "md"}
            script += ' of type {' + ", ".join([f'"{_escape_applescript_string(ext)}"' for ext in file_types]) + '}'
    script += '\nPOSIX path of chosenFile'

    result = run_osascript(script)
    if result:
        set_last_cwd(result)
    return result


def open_multiple(title=strings.open_multiple, start_dir=None, filter=None):
    """
    Open a file selection dialog for selecting multiple files using AppleScript (osascript).

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
    script = 'set chosenFiles to choose file with multiple selections allowed'
    if title:
        script += f' with prompt "{_escape_applescript_string(title)}"'
    if start_dir:
        script += f' default location POSIX file "{_escape_applescript_string(start_dir)}"'
    # File type filtering as above
    if filter:
        file_types = []
        if isinstance(filter, str):
            if filter.startswith("*."):
                ext = filter[2:]
                file_types.append(ext)
        elif isinstance(filter, list):
            for f in filter:
                if isinstance(f, str) and f.startswith("*."):
                    file_types.append(f[2:])
        elif isinstance(filter, dict):
            for value in filter.values():
                if isinstance(value, str) and value.startswith("*."):
                    file_types.append(value[2:])
                elif isinstance(value, list):
                    for v in value:
                        if isinstance(v, str) and v.startswith("*."):
                            file_types.append(v[2:])
        if file_types:
            script += ' of type {' + ", ".join([f'"{_escape_applescript_string(ext)}"' for ext in file_types]) + '}'
    script += '\nset posixList to {}\nrepeat with f in chosenFiles\nset end of posixList to POSIX path of f\nend repeat\nreturn posixList as string'

    result = run_osascript(script)
    if result:
        # AppleScript returns a comma-separated list
        split_result = [s.strip() for s in result.split(",")]
        if split_result:
            set_last_cwd(split_result[0])
            return split_result
    return []


def save_file(title=strings.save_file, start_dir=None):
    """
    Open a save file dialog using AppleScript (osascript).

    Args:
        title (str, optional): The title of the save file dialog.
            Default is 'Enter the name of the file to save to'
        start_dir (str, optional): The starting directory for the dialog.

    Returns:
        str: The selected file's path for saving.

    Example:
        result = save_file(title="Save file", start_dir="/path/to/starting/directory")
    """
    script = 'set saveFile to choose file name'
    if title:
        script += f' with prompt "{_escape_applescript_string(title)}"'
    if start_dir:
        script += f' default location POSIX file "{_escape_applescript_string(start_dir)}"'
    script += '\nPOSIX path of saveFile'

    result = run_osascript(script)
    if result:
        set_last_cwd(result)
    return result


def choose_folder(title=strings.choose_folder, start_dir=None):
    """
    Open a folder selection dialog using AppleScript (osascript).

    Args:
        title (str, optional): The title of the folder selection dialog.
            Default is 'Choose a folder'
        start_dir (str, optional): The starting directory for the dialog.

    Returns:
        str: The selected folder's path.

    Example:
        result = choose_folder(title="Select folder", start_dir="/path/to/starting/directory")
    """
    script = 'set chosenFolder to choose folder'
    if title:
        script += f' with prompt "{_escape_applescript_string(title)}"'
    if start_dir:
        script += f' default location POSIX file "{_escape_applescript_string(start_dir)}"'
    script += '\nPOSIX path of chosenFolder'

    result = run_osascript(script)
    if result:
        set_last_cwd(result)
    return result


__all__ = ['open_file', 'open_multiple', 'save_file', 'choose_folder']
