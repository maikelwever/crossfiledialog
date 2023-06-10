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

Licensed under the GNU GPL 3.0
