import os
import uuid
import ctypes

from crossfiledialog import strings
from crossfiledialog.exceptions import FileDialogException


class Win32Exception(FileDialogException):
    pass


ole32 = ctypes.windll.ole32
shell32 = ctypes.windll.shell32

S_OK = 0
CLSCTX_INPROC_SERVER = 1
COINIT_APARTMENTTHREADED = 0x2

# FILEOPENDIALOGOPTIONS (FOS_*) — see IFileDialog::SetOptions.
FOS_OVERWRITEPROMPT = 0x00000002
FOS_NOCHANGEDIR = 0x00000008
FOS_PICKFOLDERS = 0x00000020
FOS_FORCEFILESYSTEM = 0x00000040
FOS_ALLOWMULTISELECT = 0x00000200
FOS_PATHMUSTEXIST = 0x00000800
FOS_FILEMUSTEXIST = 0x00001000

# IShellItem::GetDisplayName form.
SIGDN_FILESYSPATH = 0x80058000


def _guid(s: str):
    # Pack a GUID string into the 16-byte little-endian struct COM expects.
    return (ctypes.c_byte * 16)(*uuid.UUID(s).bytes_le)


CLSID_FileOpenDialog = _guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")
CLSID_FileSaveDialog = _guid("C0B4E2F3-BA21-4773-8DBA-335EC946EB8B")
IID_IFileOpenDialog = _guid("D57C7288-D4AD-4768-BE02-9D969532D960")
IID_IFileSaveDialog = _guid("84BCCD23-5FDE-4CDB-AEA4-AF64B83D78AB")
IID_IShellItem = _guid("43826D1E-E718-42EE-BC55-A1E261C37BFE")


# IFileDialog vtable indices (inherited by IFileOpenDialog / IFileSaveDialog).
# Layout: IUnknown (0..2) + IModalWindow (3) + IFileDialog (4..26) + IFileOpenDialog (27..28).
_VT_RELEASE = 2
_VT_SHOW = 3
_VT_SETFILETYPES = 4
_VT_SETOPTIONS = 9
_VT_SETFOLDER = 12
_VT_SETFILENAME = 15
_VT_SETTITLE = 17
_VT_GETRESULT = 20
_VT_GETRESULTS = 27  # IFileOpenDialog only

# IShellItem vtable indices.
_VT_ITEM_GETDISPLAYNAME = 5

# IShellItemArray vtable indices.
_VT_ARR_GETCOUNT = 7
_VT_ARR_GETITEM = 8


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


class _ComObj:
    """Thin wrapper over a COM interface pointer with vtable-call and release helpers."""

    def __init__(self, ptr):
        self.ptr = ptr
        # vt = *(void**)ptr  — the object's vtable.
        self._vt = ctypes.cast(
            ctypes.cast(ptr, ctypes.POINTER(ctypes.c_void_p))[0],
            ctypes.POINTER(ctypes.c_void_p),
        )

    def call(self, index: int, restype, *argspec):
        # argspec is alternating (ctype, value) pairs.
        argtypes = [ctypes.c_void_p] + list(argspec[0::2])
        args = [self.ptr] + list(argspec[1::2])
        fn = ctypes.WINFUNCTYPE(restype, *argtypes)(self._vt[index])
        return fn(*args)

    def release(self):
        if self.ptr:
            self.call(_VT_RELEASE, ctypes.c_ulong)
            self.ptr = None


def _co_create(clsid, iid) -> _ComObj:
    # CoCreateInstance wrapper.
    ptr = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(
        clsid, None, CLSCTX_INPROC_SERVER, iid, ctypes.byref(ptr)
    )
    if hr != S_OK or not ptr:
        raise Win32Exception(
            f"CoCreateInstance failed (HRESULT=0x{hr & 0xFFFFFFFF:08X})"
        )
    return _ComObj(ptr)


def _shell_item_from_path(path: str):
    # Create an IShellItem from a filesystem path, or None if it can't be parsed.
    ptr = ctypes.c_void_p()
    hr = shell32.SHCreateItemFromParsingName(
        ctypes.c_wchar_p(path),
        None,
        IID_IShellItem,
        ctypes.byref(ptr),
    )
    if hr != S_OK or not ptr:
        return None
    return _ComObj(ptr)


def _shell_item_path(item: _ComObj) -> str:
    # IShellItem::GetDisplayName(SIGDN_FILESYSPATH) -> Python str (or None).
    name_ptr = ctypes.c_wchar_p()
    fn = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_wchar_p),
    )(item._vt[_VT_ITEM_GETDISPLAYNAME])
    hr = fn(item.ptr, SIGDN_FILESYSPATH, ctypes.byref(name_ptr))
    if hr != S_OK or not name_ptr.value:
        return None
    path = name_ptr.value
    # The string was allocated with CoTaskMemAlloc; the caller owns it.
    ole32.CoTaskMemFree(ctypes.cast(name_ptr, ctypes.c_void_p))
    return path


# COMDLG_FILTERSPEC { LPCWSTR pszName; LPCWSTR pszSpec; } — used by SetFileTypes.
class _FilterSpec(ctypes.Structure):
    _fields_ = [("pszName", ctypes.c_wchar_p), ("pszSpec", ctypes.c_wchar_p)]


last_cwd = None


def get_preferred_cwd():
    possible_cwd = os.environ.get("FILEDIALOG_CWD", "")
    if possible_cwd:
        return possible_cwd
    return last_cwd


def set_last_cwd(cwd):
    # cwd is a file path; remember its containing directory.
    global last_cwd
    last_cwd = os.path.dirname(cwd)


def _remember_dir(path: str):
    # path is already a directory; store it as-is.
    global last_cwd
    last_cwd = path


def _normalize_filter(filter) -> list:
    if isinstance(filter, str):
        # Single wildcard: label and pattern are identical.
        return [(filter, filter)]

    if isinstance(filter, list):
        if not filter:
            return []
        if isinstance(filter[0], str):
            # Flat list of wildcards -> one entry, patterns joined by ';'.
            joined = ";".join(filter)
            return [(joined, joined)]
        if isinstance(filter[0], list):
            # List of lists -> one entry per inner list.
            return [(";".join(g), ";".join(g)) for g in filter]
        raise ValueError("Invalid filter")

    if isinstance(filter, dict):
        out = []
        for label, value in filter.items():
            if isinstance(value, str):
                out.append((label, value))
            elif isinstance(value, list):
                out.append((label, ";".join(value)))
            else:
                raise ValueError("Invalid filter")
        return out

    raise ValueError("Invalid filter")


def _apply_filter(dialog: _ComObj, filter):
    if not filter:
        return
    specs = _normalize_filter(filter)
    if not specs:
        return
    arr = (_FilterSpec * len(specs))(*[_FilterSpec(lbl, pat) for lbl, pat in specs])
    dialog.call(
        _VT_SETFILETYPES,
        ctypes.c_int,
        ctypes.c_uint,
        len(specs),
        ctypes.POINTER(_FilterSpec),
        arr,
    )


# ---------------------------------------------------------------------------
# Shared dialog setup
# ---------------------------------------------------------------------------


def _configure_dialog(dialog: _ComObj, title, start_dir, filter, extra_options: int):
    # Always force filesystem paths and require existing paths; callers add the rest.
    dialog.call(
        _VT_SETOPTIONS,
        ctypes.c_int,
        ctypes.c_uint,
        FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST | FOS_NOCHANGEDIR | extra_options,
    )

    if title:
        dialog.call(_VT_SETTITLE, ctypes.c_int, ctypes.c_wchar_p, title)

    initial = start_dir or get_preferred_cwd()
    if initial and os.path.isdir(initial):
        folder = _shell_item_from_path(initial)
        if folder is not None:
            dialog.call(_VT_SETFOLDER, ctypes.c_int, ctypes.c_void_p, folder.ptr)
            folder.release()

    _apply_filter(dialog, filter)


def _show_and_get_single(dialog: _ComObj) -> str:
    # Show the dialog and return the single selected path, or None on cancel.
    hr = dialog.call(_VT_SHOW, ctypes.c_int, ctypes.c_void_p, None)
    if hr != S_OK:
        return None

    result_ptr = ctypes.c_void_p()
    hr = dialog.call(
        _VT_GETRESULT,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.byref(result_ptr),
    )
    if hr != S_OK or not result_ptr:
        return None

    item = _ComObj(result_ptr)
    try:
        return _shell_item_path(item)
    finally:
        item.release()


# ---------------------------------------------------------------------------
# DPI awareness
# ---------------------------------------------------------------------------
# Without DPI awareness, Windows renders this process's dialogs at 96 DPI and
# then bitmap-stretches them to the display DPI, which produces blurry text
# on high-DPI screens. Applying awareness around Show() makes the Common Item
# Dialog render natively at the target DPI.

# DPI_AWARENESS_CONTEXT pseudo-handles, used by SetThreadDpiAwarenessContext
# (Win10 1607+) and SetProcessDpiAwarenessContext (Win10 1703+).
_DPI_PER_MONITOR_AWARE_V2 = -4
_DPI_PER_MONITOR_AWARE = -3
_DPI_SYSTEM_AWARE = -2

# PROCESS_DPI_AWARENESS values for shcore!SetProcessDpiAwareness (Win8.1+).
_PROCESS_PER_MONITOR_DPI_AWARE = 2
_PROCESS_SYSTEM_DPI_AWARE = 1

_process_dpi_initialized = False


def _set_process_dpi_aware_once():
    """Apply process-wide DPI awareness exactly once. Fallback for pre-Win10 1607."""
    global _process_dpi_initialized
    if _process_dpi_initialized:
        return
    _process_dpi_initialized = True

    user32 = ctypes.windll.user32

    # Win10 1703+: per-monitor v2 > per-monitor > system, in that order.
    fn = getattr(user32, "SetProcessDpiAwarenessContext", None)
    if fn is not None:
        fn.restype = ctypes.c_int
        fn.argtypes = [ctypes.c_void_p]
        for ctx in (_DPI_PER_MONITOR_AWARE_V2, _DPI_PER_MONITOR_AWARE, _DPI_SYSTEM_AWARE):
            if fn(ctypes.c_void_p(ctx)):
                return

    # Win8.1+: shcore!SetProcessDpiAwareness. shcore.dll is absent on Win7/Vista.
    try:
        shcore = ctypes.windll.shcore
    except OSError:
        shcore = None
    fn = getattr(shcore, "SetProcessDpiAwareness", None) if shcore else None
    if fn is not None:
        fn.restype = ctypes.c_int
        fn.argtypes = [ctypes.c_int]
        for level in (_PROCESS_PER_MONITOR_DPI_AWARE, _PROCESS_SYSTEM_DPI_AWARE):
            if fn(level) == S_OK:
                return

    # Vista+: system-DPI awareness only.
    fn = getattr(user32, "SetProcessDPIAware", None)
    if fn is not None:
        fn()


class _DpiAware:
    """Make dialog windows DPI-aware for the duration of a `with` block.

    On Win10 1607+, the change is scoped to the current thread and reverted on
    exit, leaving the host app's DPI mode untouched. On older Windows (down to
    Vista), falls back to a one-time process-wide change.
    """

    def __init__(self):
        self._prev = None
        self._set_thread = None

    def __enter__(self):
        user32 = ctypes.windll.user32
        fn = getattr(user32, "SetThreadDpiAwarenessContext", None)
        if fn is None:
            _set_process_dpi_aware_once()
            return self

        fn.restype = ctypes.c_void_p
        fn.argtypes = [ctypes.c_void_p]
        for ctx in (_DPI_PER_MONITOR_AWARE_V2, _DPI_PER_MONITOR_AWARE, _DPI_SYSTEM_AWARE):
            prev = fn(ctypes.c_void_p(ctx))
            if prev:  # non-NULL pseudo-handle = previous context, success.
                self._prev = prev
                self._set_thread = fn
                return self

        # Thread-scoped attempt failed for every level; fall back to process-wide.
        _set_process_dpi_aware_once()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._set_thread is not None and self._prev is not None:
            self._set_thread(ctypes.c_void_p(self._prev))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def open_file(title=strings.open_file, start_dir=None, filter=None):
    """
    Open a file selection dialog using the Common Item Dialog API.

    Args:
        title (str, optional): Dialog title. Default is 'Choose a file'.
        start_dir (str, optional): Starting directory.
        filter (str, list, dict, optional): File-type filter.

    Returns:
        str: Selected file path, or None if cancelled.
    """
    ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    path = None
    try:
        with _DpiAware():
            dialog = _co_create(CLSID_FileOpenDialog, IID_IFileOpenDialog)
            try:
                _configure_dialog(dialog, title, start_dir, filter, FOS_FILEMUSTEXIST)
                path = _show_and_get_single(dialog)
            finally:
                dialog.release()
    finally:
        ole32.CoUninitialize()

    if path:
        set_last_cwd(path)
    return path


def open_multiple(title=strings.open_multiple, start_dir=None, filter=None) -> list:
    """
    Open a multi-select file dialog using the Common Item Dialog API.

    Args:
        title (str, optional): Dialog title. Default is 'Choose one or more files'.
        start_dir (str, optional): Starting directory.
        filter (str, list, dict, optional): File-type filter.

    Returns:
        list[str]: Selected file paths (empty list if cancelled).
    """
    ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    paths = []
    try:
        with _DpiAware():
            dialog = _co_create(CLSID_FileOpenDialog, IID_IFileOpenDialog)
            try:
                _configure_dialog(
                    dialog,
                    title,
                    start_dir,
                    filter,
                    FOS_FILEMUSTEXIST | FOS_ALLOWMULTISELECT,
                )

                hr = dialog.call(_VT_SHOW, ctypes.c_int, ctypes.c_void_p, None)
                if hr != S_OK:
                    return []

                # IFileOpenDialog::GetResults -> IShellItemArray
                arr_ptr = ctypes.c_void_p()
                hr = dialog.call(
                    _VT_GETRESULTS,
                    ctypes.c_int,
                    ctypes.POINTER(ctypes.c_void_p),
                    ctypes.byref(arr_ptr),
                )
                if hr != S_OK or not arr_ptr:
                    return []

                arr = _ComObj(arr_ptr)
                try:
                    count = ctypes.c_uint(0)
                    arr.call(
                        _VT_ARR_GETCOUNT,
                        ctypes.c_int,
                        ctypes.POINTER(ctypes.c_uint),
                        ctypes.byref(count),
                    )
                    for i in range(count.value):
                        item_ptr = ctypes.c_void_p()
                        hr = arr.call(
                            _VT_ARR_GETITEM,
                            ctypes.c_int,
                            ctypes.c_uint,
                            i,
                            ctypes.POINTER(ctypes.c_void_p),
                            ctypes.byref(item_ptr),
                        )
                        if hr != S_OK or not item_ptr:
                            continue
                        item = _ComObj(item_ptr)
                        try:
                            p = _shell_item_path(item)
                            if p:
                                paths.append(p)
                        finally:
                            item.release()
                finally:
                    arr.release()
            finally:
                dialog.release()
    finally:
        ole32.CoUninitialize()

    if paths:
        set_last_cwd(paths[0])
    return paths


def save_file(title=strings.save_file, start_dir=None, filter=None, default_name=None):
    """
    Open a save-as dialog using the Common Item Dialog API.
 
    Args:
        title (str, optional): Dialog title.
            Default is 'Enter the name of the file to save to'.
        start_dir (str, optional): Starting directory.
        filter (str, list, dict, optional): File-type filter.
        default_name (str, optional): Pre-filled filename. May be either a
            bare filename ('report.pdf') or a full path; if a full path is
            given and start_dir is not set, its directory becomes start_dir.
 
    Returns:
        str: Path to save to, or None if cancelled.
    """
    # Split default_name into folder + filename if it carries a directory part.
    prefill_name = None
    if default_name:
        head, tail = os.path.split(default_name)
        prefill_name = tail or None
        if head and not start_dir:
            start_dir = head
 
    ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    path = None
    try:
        with _DpiAware():
            dialog = _co_create(CLSID_FileSaveDialog, IID_IFileSaveDialog)
            try:
                _configure_dialog(dialog, title, start_dir, filter, FOS_OVERWRITEPROMPT)
                if prefill_name:
                    dialog.call(_VT_SETFILENAME, ctypes.c_int, ctypes.c_wchar_p, prefill_name)
                path = _show_and_get_single(dialog)
            finally:
                dialog.release()
    finally:
        ole32.CoUninitialize()
 
    if path:
        set_last_cwd(path)
    return path


def choose_folder(title: str = "Select folder", start_dir: str = None) -> str:
    """
    Open a folder selection dialog using Common Item Dialog API.

    Args:
        title (str, optional): Dialog title. Default is 'Choose a folder'.
        start_dir (str, optional): Starting directory.

    Returns:
        str: Selected folder path, or None if cancelled.
    """
    ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    path = None
    try:
        with _DpiAware():
            dialog = _co_create(CLSID_FileOpenDialog, IID_IFileOpenDialog)
            try:
                _configure_dialog(
                    dialog, title, start_dir, None, FOS_PICKFOLDERS | FOS_FILEMUSTEXIST
                )
                path = _show_and_get_single(dialog)
            finally:
                dialog.release()
    finally:
        ole32.CoUninitialize()

    if path:
        _remember_dir(path)
    return path


__all__ = ["open_file", "open_multiple", "save_file", "choose_folder"]
