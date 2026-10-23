# **************************************************************************
# *                                                                        *
# *   GDMLLog - warnings/errors from GDML export, to the Report View and    *
# *   to a log file beside the exported file                               *
# *                                                                        *
# *   Works the same on Windows, Linux and macOS: only Python's logging    *
# *   and pathlib are used, files are UTF-8, and the log file is always    *
# *   closed when the export finishes (so it is never left locked on       *
# *   Windows).                                                            *
# *                                                                        *
# *   Usage (exportGDML.export):                                           *
# *       logPath = GDMLLog.start(filepath)    # "<file>.gdml.log"         *
# *       try:                                                             *
# *           ... export ...                                               *
# *       finally:                                                         *
# *           GDMLLog.stop()                                               *
# *                                                                        *
# *   and anywhere during the export:                                      *
# *       GDMLLog.warning("...")  -> Report View (orange) + log file       *
# *       GDMLLog.error("...")    -> Report View (red) + log file          *
# *       GDMLLog.info("...")     -> log file only                         *
# *                                                                        *
# *   The log file can be turned off with the GDML preference             *
# *   ExportLogFile (default on).  If the export folder is not writable    *
# *   the log goes to <FreeCAD user data>/GDML/logs/ instead.              *
# *                                                                        *
# **************************************************************************

import datetime
import logging
from pathlib import Path

import FreeCAD

PARAMS = "User parameter:BaseApp/Preferences/Mod/GDML"
LOG_SUFFIX = ".log"

_logger = logging.getLogger("freecad.gdml.export")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False   # FreeCAD or other addons may configure the root logger

_fileHandler = None
_logPath = None
_counts = {}


class _ReportViewHandler(logging.Handler):
    """Send warnings and errors to FreeCAD's Report View, as before."""

    def emit(self, record):
        try:
            msg = self.format(record) + "\n"
            if record.levelno >= logging.ERROR:
                FreeCAD.Console.PrintError(msg)
            elif record.levelno >= logging.WARNING:
                FreeCAD.Console.PrintWarning(msg)
            else:
                FreeCAD.Console.PrintLog(msg)
        except Exception:
            self.handleError(record)


class _CountingHandler(logging.Handler):
    """Count messages per level, so callers can report a summary."""

    def emit(self, record):
        _counts[record.levelname] = _counts.get(record.levelname, 0) + 1


def _ensureConsoleHandlers():
    if not any(isinstance(h, _ReportViewHandler) for h in _logger.handlers):
        h = _ReportViewHandler(level=logging.WARNING)
        h.setFormatter(logging.Formatter("GDML export: %(message)s"))
        _logger.addHandler(h)
    if not any(isinstance(h, _CountingHandler) for h in _logger.handlers):
        _logger.addHandler(_CountingHandler(level=logging.DEBUG))


def fileLoggingEnabled():
    try:
        return FreeCAD.ParamGet(PARAMS).GetBool("ExportLogFile", True)
    except Exception:
        return True


def logPathFor(exportPath):
    """'<dir>/name.gdml' -> '<dir>/name.gdml.log'"""
    p = Path(exportPath)
    return p.with_name(p.name + LOG_SUFFIX)


def _fallbackDir():
    return Path(FreeCAD.getUserAppDataDir()) / "GDML" / "logs"


def _openFileHandler(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # mode "w": each export replaces its own log; newline handling is the
    # platform's (\r\n on Windows), which every text editor reads
    h = logging.FileHandler(str(path), mode="w", encoding="utf-8")
    h.setLevel(logging.DEBUG)
    h.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    return h


def start(exportPath):
    """Start logging for one export.  Returns the log file path, or None
    if file logging is off or no log file could be opened."""
    global _fileHandler, _logPath
    stop()                      # never leave a previous export's file open
    _ensureConsoleHandlers()
    _counts.clear()
    if not fileLoggingEnabled():
        return None
    primary = logPathFor(exportPath)
    for path in (primary, _fallbackDir() / primary.name):
        try:
            _fileHandler = _openFileHandler(path)
            _logPath = path
            break
        except OSError as e:
            FreeCAD.Console.PrintLog(f"GDMLLog: cannot write {path}: {e}\n")
    if _fileHandler is None:
        return None
    _logger.addHandler(_fileHandler)
    _logger.info(f"GDML export of {Path(exportPath).name} "
                 f"started {datetime.datetime.now().isoformat(timespec='seconds')}, "
                 f"FreeCAD {'.'.join(FreeCAD.Version()[:3])}")
    return _logPath


def stop():
    """Finish the current export's log and close its file."""
    global _fileHandler, _logPath
    if _fileHandler is not None:
        n = _counts.get("WARNING", 0)
        e = _counts.get("ERROR", 0)
        _logger.info(f"finished: {e} error(s), {n} warning(s)")
        _logger.removeHandler(_fileHandler)
        _fileHandler.close()
        _fileHandler = None
    path, _logPath = _logPath, None
    return path


def currentLogPath():
    return _logPath


def counts():
    """{'WARNING': n, 'ERROR': m, ...} for the current or last export."""
    return dict(_counts)


def info(msg):
    _ensureConsoleHandlers()
    _logger.info(msg)


def warning(msg):
    _ensureConsoleHandlers()
    _logger.warning(msg)


def error(msg):
    _ensureConsoleHandlers()
    _logger.error(msg)
