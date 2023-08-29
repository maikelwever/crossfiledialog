CrossFileDialog
===============

A Python wrapper for opening files and folders with the native file dialog.

Makes it easy to prompt the user with a native filepicker on all supported platforms.


Currently supports:

 - Zenity (GTK)
 - KDialog (KDE)
 - Windows 2000 and newer (via PyWin32)

Basic API usage:

```python
import crossfiledialog

filename = crossfiledialog.open_file()
multiple_filenames = crossfiledialog.open_multiple()
save_filename = crossfiledialog.save_file()
foldername = crossfiledialog.choose_folder()
```

## Documentation
```python
crossfiledialog.open_file(title, start_dir, filter) -> str
```
Open a file selection dialog for selecting a file.

Parameters:
 - title (str, optional) — The title of the file selection dialog. Default is 'Choose a file'
 - start_dir (str, optional) — The starting directory for the dialog.
 - filter (str, list, dict, optional) — The filter for file types to display. It can be either:
   - a single wildcard (e.g.: `"*.py"`, all files are displayed ending .py)
   - a list of wildcards (e.g.: `["*.py" "*.md"]`, all files are displayed ending either .py or .md)
   - a list of list optional one or more wildcards (e.g.: `[["*.py", "*.md"], ["*.txt"]]`, 
 user can switch between (.py, .md) and (.txt))
   - a dictionary mapping descriptions to wildcards (e.g.: `{"PDF-Files": "*.pdf", "Python Project": ["\*.py", "*.md"]}`)

Returns:
 - str: The selected file's path.

---

```python
crossfiledialog.open_multiple(title, start_dir, filter) -> list[str]
```
Open a file selection dialog for selecting multiple files.

Parameters:
 - title (str, optional) — The title of the file selection dialog. Default is 'Choose one or more files'
 - start_dir (str, optional) — The starting directory for the dialog.
 - filter (str, list, dict, optional) — The filter for file types to display. It can be either:
   - a single wildcard (e.g.: `"*.py"`, all files are displayed ending .py)
   - a list of wildcards (e.g.: `["*.py" "*.md"]`, all files are displayed ending either .py or .md)
   - a list of list optional one or more wildcards (e.g.: `[["*.py", "*.md"], ["*.txt"]]`, 
 user can switch between (.py, .md) and (.txt))
   - a dictionary mapping descriptions to wildcards (e.g.: `{"PDF-Files": "*.pdf", "Python Project": ["\*.py", "*.md"]}`)

Returns:
 - list[str]: A list of selected file paths.

---

```python
crossfiledialog.save_file(title, start_dir) -> str
```
Open a save file dialog.

Parameters:
 - title (str, optional) — The title of the file selection dialog. Default is 'Enter the name of the file to save to'
 - start_dir (str, optional) — The starting directory for the dialog.

Returns:
 - str: The selected file's path for saving.

---

```python
crossfiledialog.save_file(title, start_dir) -> str
```
Open a folder selection dialog.

Parameters:
 - title (str, optional) — The title of the file selection dialog. Default is 'Choose a folder'
 - start_dir (str, optional) — The starting directory for the dialog.

Returns:
 - str: The selected folder's path.

## Licence
Licensed under the GNU GPL 3.0
