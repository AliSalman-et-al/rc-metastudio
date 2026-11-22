import ctypes
import locale
import os
from pathlib import Path
import sys
import tempfile

class AnalysisBackendUnavailableError(RuntimeError):
    """Raised when the configured R analysis backend cannot service requests."""


_READY = False


def is_ready() -> bool:
    return _READY


def mark_ready() -> None:
    global _READY
    _READY = True


def mark_unavailable() -> None:
    global _READY
    _READY = False


def _configure_private_runtime_directories(root):
    bundle = Path(root).resolve()
    base = (
        Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "RCMetaStudio" / "runtime"
    )
    if base.resolve().is_relative_to(bundle.parent):
        raise RuntimeError(
            "Frozen runtime HOME must be outside the application bundle."
        )
    home = base / "home"
    temporary = base / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    temporary.mkdir(parents=True, exist_ok=True)
    for path in (home, temporary):
        descriptor, name = tempfile.mkstemp(prefix=".write-probe-", dir=path)
        os.close(descriptor)
        Path(name).unlink()
    os.environ["HOME"] = str(home)
    os.environ["TMPDIR"] = str(temporary)
    os.environ["TMP"] = str(temporary)
    os.environ["TEMP"] = str(temporary)
    tempfile.tempdir = str(temporary)


def macos_r_framework_version(r_version: str) -> str:
    """Return the stable major.minor directory name for an R framework."""
    parts = r_version.split(".")
    if len(parts) < 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"invalid R version for a macOS framework: {r_version!r}")
    return ".".join(parts[:2])


def _runtime_candidates(root, frozen):
    if frozen and sys.platform == "linux":
        return [os.path.abspath(os.path.join(root, "..", "R"))]
    candidates = [
        os.path.join(root, "..", "Frameworks", "R.framework", "Resources"),
        os.path.join(root, "R"),
    ]
    if not frozen:
        candidates.insert(0, os.environ.get("RCMS_R_HOME"))
    return candidates


def _configure_r_home(root, frozen):
    override = os.environ.get("RCMS_R_HOME") if not frozen else None
    if override is not None and (not override or not os.path.isdir(os.path.join(override, "bin"))):
        raise RuntimeError(f"Invalid RCMS_R_HOME: {override!r}; expected an R home with bin/.")
    r_home = (
        os.path.abspath(override) if override is not None else
        _first_existing(_runtime_candidates(root, frozen), required_child="bin")
    )
    if not r_home:
        if frozen:
            raise RuntimeError("Frozen application is missing its private R runtime.")
        return None
    if frozen and sys.platform == "linux" and not os.path.isfile(
        os.path.join(r_home, "lib", "libR.so")
    ):
        raise RuntimeError("Frozen Linux application is missing its private libR.so.")
    os.environ["R_HOME"] = r_home
    _configure_r_executable_path(r_home, frozen)
    return r_home


def _configure_r_executable_path(r_home, frozen):
    paths = [os.path.join(r_home, "bin", "x64"), os.path.join(r_home, "bin")]
    if frozen and sys.platform != "win32":
        paths.extend(("/usr/bin", "/bin", "/usr/sbin", "/sbin"))
    _prepend_path(paths, preserve_existing=not frozen)


def _configure_r_libraries(root, r_home, frozen):
    candidates = [
        os.path.join(r_home, "library") if r_home else None,
        os.path.join(root, "..", "Frameworks", "R.framework", "Resources", "library"),
        os.path.join(root, "R", "library"),
    ]
    if not frozen:
        candidates.insert(0, os.environ.get("RCMS_R_LIBS"))
    override = os.environ.get("RCMS_R_LIBS") if not frozen else None
    if override is not None and (not override or not os.path.isdir(os.path.join(override, "RCMetaR"))):
        raise RuntimeError(f"Invalid RCMS_R_LIBS: {override!r}; expected a library containing RCMetaR/.")
    r_libs = (
        os.path.abspath(override) if override is not None else
        _first_existing(candidates, required_child="RCMetaR")
    )
    if r_libs:
        os.environ["R_LIBS"] = r_libs
        os.environ["R_LIBS_USER"] = r_libs
    elif frozen:
        raise RuntimeError("Frozen application is missing its private RCMetaR library.")
    return r_libs


def _set_windows_processor_architecture():
    if os.environ.get("PROCESSOR_ARCHITECTURE"):
        return
    # cli's Windows shutdown code expects this even with a minimal caller environment.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    query = kernel32.IsWow64Process2
    query.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_ushort), ctypes.POINTER(ctypes.c_ushort)
    ]
    query.restype = ctypes.c_int
    process_machine = ctypes.c_ushort()
    native_machine = ctypes.c_ushort()
    if not query(ctypes.c_void_p(-1), ctypes.byref(process_machine), ctypes.byref(native_machine)):
        raise OSError(ctypes.get_last_error(), "IsWow64Process2 failed")
    os.environ["PROCESSOR_ARCHITECTURE"] = {
        0x014C: "x86", 0x8664: "AMD64", 0xAA64: "ARM64"
    }[native_machine.value]


def _set_r_environment():
    if sys.platform == "win32":
        _set_windows_processor_architecture()
        for name in (
            "LC_ALL",
            "LC_COLLATE",
            "LC_CTYPE",
            "LC_MONETARY",
            "LC_TIME",
            "LANG",
        ):
            if os.environ.get(name, "").lower() in {"c.utf-8", "c.utf8"}:
                os.environ.pop(name, None)
    os.environ["R_ENVIRON_USER"] = os.devnull
    os.environ["R_PROFILE_USER"] = os.devnull
    os.environ["R_ENVIRON"] = os.devnull
    os.environ["R_PROFILE"] = os.devnull
    os.environ["R_DEFAULT_PACKAGES"] = "utils,grDevices,graphics,stats,methods"
    os.environ["LC_NUMERIC"] = "C"
    locale.setlocale(locale.LC_NUMERIC, "C")


def configure_bundled_r_environment(app_root=None):
    """Select the private interpreter and package library for the worker."""
    root = app_root or _app_root()
    frozen = bool(getattr(sys, "frozen", False))
    if frozen:
        _configure_private_runtime_directories(root)
    r_home = _configure_r_home(root, frozen)
    _configure_r_libraries(root, r_home, frozen)
    _set_r_environment()
    return {"R_HOME": os.environ.get("R_HOME"), "R_LIBS": os.environ.get("R_LIBS")}


def _app_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return _repo_root()


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _first_existing(candidates, required_child=None):
    for candidate in candidates:
        if not candidate:
            continue
        if required_child is None and os.path.exists(candidate):
            return candidate
        if required_child is not None and os.path.exists(
            os.path.join(candidate, required_child)
        ):
            return candidate
    return None


def _prepend_path(paths, preserve_existing=True):
    existing = os.environ.get("PATH", "") if preserve_existing else ""
    path_parts = []
    seen = set()
    for path in paths:
        normalized = os.path.normcase(os.path.abspath(path))
        if os.path.exists(path) and normalized not in seen:
            path_parts.append(path)
            seen.add(normalized)
    os.environ["PATH"] = os.pathsep.join(path_parts + ([existing] if existing else []))
