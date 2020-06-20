FileDialog
==========

A Python wrapper for opening files and folders with the native file dialog.

Makes it easy to prompt the user with a native filepicker on all supported platforms.


Currently supports:

 - Zenity (GTK)
 - KDialog (KDE)
 - Windows 2000 and newer (via PyWin32)



Basic API usage:

```python
import filedialog

filename = filedialog.open_file()
multiple_filenames = filedialog.open_multiple()
save_filename = filedialog.save_file()
foldername = filedialog.choose_folder()
```

Licensed under the GNU GPL 3.0
