"""Bounded Windows API probes for the R0 isolation-launcher Spike.

This module is deliberately *not* a production provider.  It exercises only
synthetic processes and a temporary zero-capability AppContainer profile.  It
does not launch Python inside an AppContainer, change network policy, grant
filesystem ACLs, or claim that untrusted code is safely sandboxed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from uuid import uuid4


class WindowsIsolationSpikeError(RuntimeError):
    """A Windows isolation primitive could not be established or observed."""


@dataclass(frozen=True)
class AppContainerProfileProbe:
    state: str
    profile_name: str
    create_hresult: str
    delete_hresult: str | None
    detail: str


@dataclass(frozen=True)
class JobTreeProbe:
    state: str
    parent_pid: int
    child_pid: int
    parent_in_job: bool
    child_in_job: bool
    active_pids_before_terminate: tuple[int, ...]
    active_pids_after_terminate: tuple[int, ...]
    parent_exited: bool
    child_exited: bool
    detail: str


@dataclass(frozen=True)
class AppContainerPythonProbe:
    state: str
    profile_name: str
    create_hresult: str
    delete_hresult: str | None
    process_pid: int
    token_is_appcontainer: bool
    process_in_job: bool
    exit_code: int | None
    active_pids_after_exit: tuple[int, ...]
    detail: str


if os.name == "nt":
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _userenv = ctypes.WinDLL("userenv", use_last_error=True)
    _advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

    _ULONG_PTR = ctypes.c_size_t
    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    _JOB_OBJECT_BASIC_PROCESS_ID_LIST = 3
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _SYNCHRONIZE = 0x00100000
    _WAIT_TIMEOUT = 0x00000102
    _S_OK = 0
    _TOKEN_QUERY = 0x0008
    _TOKEN_IS_APPCONTAINER = 29
    _EXTENDED_STARTUPINFO_PRESENT = 0x00080000
    _CREATE_SUSPENDED = 0x00000004
    _WAIT_OBJECT_0 = 0
    _INVALID_DWORD = 0xFFFFFFFF
    _PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", _ULONG_PTR),
            ("MaximumWorkingSetSize", _ULONG_PTR),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", _ULONG_PTR),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", _ULONG_PTR),
            ("JobMemoryLimit", _ULONG_PTR),
            ("PeakProcessMemoryUsed", _ULONG_PTR),
            ("PeakJobMemoryUsed", _ULONG_PTR),
        ]

    class _PROCESS_ID_LIST_HEADER(ctypes.Structure):
        _fields_ = [
            ("NumberOfAssignedProcesses", wintypes.DWORD),
            ("NumberOfProcessIdsInList", wintypes.DWORD),
        ]

    class _SECURITY_CAPABILITIES(ctypes.Structure):
        _fields_ = [
            ("AppContainerSid", wintypes.LPVOID),
            ("Capabilities", wintypes.LPVOID),
            ("CapabilityCount", wintypes.DWORD),
            ("Reserved", wintypes.DWORD),
        ]

    class _STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class _STARTUPINFOEXW(ctypes.Structure):
        _fields_ = [("StartupInfo", _STARTUPINFOW), ("lpAttributeList", wintypes.LPVOID)]

    class _PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    _kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, wintypes.INT, wintypes.LPVOID, wintypes.DWORD]
    _kernel32.SetInformationJobObject.restype = wintypes.BOOL
    _kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    _kernel32.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    _kernel32.IsProcessInJob.restype = wintypes.BOOL
    _kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.TerminateJobObject.restype = wintypes.BOOL
    _kernel32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, wintypes.INT, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    _kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _kernel32.WaitForSingleObject.restype = wintypes.DWORD
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.LocalFree.argtypes = [wintypes.LPVOID]
    _kernel32.LocalFree.restype = wintypes.LPVOID
    _kernel32.InitializeProcThreadAttributeList.argtypes = [wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_size_t)]
    _kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
    _kernel32.UpdateProcThreadAttribute.argtypes = [wintypes.LPVOID, wintypes.DWORD, ctypes.c_size_t, wintypes.LPVOID, ctypes.c_size_t, wintypes.LPVOID, wintypes.LPVOID]
    _kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
    _kernel32.DeleteProcThreadAttributeList.argtypes = [wintypes.LPVOID]
    _kernel32.DeleteProcThreadAttributeList.restype = None
    _kernel32.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.LPVOID, wintypes.LPVOID, wintypes.BOOL, wintypes.DWORD, wintypes.LPVOID, wintypes.LPCWSTR, wintypes.LPVOID, ctypes.POINTER(_PROCESS_INFORMATION)]
    _kernel32.CreateProcessW.restype = wintypes.BOOL
    _kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    _kernel32.ResumeThread.restype = wintypes.DWORD
    _kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    _kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    _userenv.CreateAppContainerProfile.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID)]
    _userenv.CreateAppContainerProfile.restype = ctypes.c_long
    _userenv.DeleteAppContainerProfile.argtypes = [wintypes.LPCWSTR]
    _userenv.DeleteAppContainerProfile.restype = ctypes.c_long
    _advapi32.FreeSid.argtypes = [wintypes.LPVOID]
    _advapi32.FreeSid.restype = wintypes.LPVOID
    _advapi32.ConvertSidToStringSidW.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR)]
    _advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
    _advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    _advapi32.OpenProcessToken.restype = wintypes.BOOL
    _advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, wintypes.INT, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    _advapi32.GetTokenInformation.restype = wintypes.BOOL


def _require_windows() -> None:
    if os.name != "nt":
        raise WindowsIsolationSpikeError("this Spike requires Windows")


def _hresult(value: int) -> str:
    return f"0x{ctypes.c_uint32(value).value:08X}"


class WindowsJob:
    """A minimal Job Object wrapper used only by this synthetic Spike."""

    def __init__(self) -> None:
        _require_windows()
        handle = _kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise WindowsIsolationSpikeError(f"CreateJobObjectW failed: {ctypes.WinError(ctypes.get_last_error())}")
        self._handle = handle
        limits = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _kernel32.SetInformationJobObject(
            self._handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise WindowsIsolationSpikeError(f"SetInformationJobObject failed: {error}")

    def __enter__(self) -> "WindowsJob":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        if self._handle:
            handle, self._handle = self._handle, None
            if not _kernel32.CloseHandle(handle):
                raise WindowsIsolationSpikeError(f"CloseHandle(job) failed: {ctypes.WinError(ctypes.get_last_error())}")

    def assign_process_handle(self, handle: int) -> None:
        if not _kernel32.AssignProcessToJobObject(self._handle, wintypes.HANDLE(handle)):
            raise WindowsIsolationSpikeError(f"AssignProcessToJobObject failed: {ctypes.WinError(ctypes.get_last_error())}")

    def contains_process_handle(self, handle: int) -> bool:
        in_job = wintypes.BOOL()
        if not _kernel32.IsProcessInJob(wintypes.HANDLE(handle), self._handle, ctypes.byref(in_job)):
            raise WindowsIsolationSpikeError(f"IsProcessInJob failed: {ctypes.WinError(ctypes.get_last_error())}")
        return bool(in_job.value)

    def contains_pid(self, pid: int) -> bool:
        handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            return self.contains_process_handle(handle)
        finally:
            _kernel32.CloseHandle(handle)

    def active_pids(self) -> tuple[int, ...]:
        capacity = 32
        buffer = ctypes.create_string_buffer(ctypes.sizeof(_PROCESS_ID_LIST_HEADER) + ctypes.sizeof(_ULONG_PTR) * capacity)
        returned = wintypes.DWORD()
        if not _kernel32.QueryInformationJobObject(
            self._handle,
            _JOB_OBJECT_BASIC_PROCESS_ID_LIST,
            buffer,
            ctypes.sizeof(buffer),
            ctypes.byref(returned),
        ):
            raise WindowsIsolationSpikeError(f"QueryInformationJobObject failed: {ctypes.WinError(ctypes.get_last_error())}")
        header = ctypes.cast(buffer, ctypes.POINTER(_PROCESS_ID_LIST_HEADER)).contents
        if header.NumberOfProcessIdsInList > capacity:
            raise WindowsIsolationSpikeError("Job process list exceeded bounded probe capacity")
        pids = (_ULONG_PTR * header.NumberOfProcessIdsInList).from_buffer(buffer, ctypes.sizeof(_PROCESS_ID_LIST_HEADER))
        return tuple(int(pid) for pid in pids)

    def terminate(self, exit_code: int = 37) -> None:
        if not _kernel32.TerminateJobObject(self._handle, exit_code):
            raise WindowsIsolationSpikeError(f"TerminateJobObject failed: {ctypes.WinError(ctypes.get_last_error())}")


def _wait_for_path(path: Path, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise WindowsIsolationSpikeError(f"timed out waiting for synthetic probe output: {path.name}")


def _pid_has_exited(pid: int) -> bool:
    _require_windows()
    handle = _kernel32.OpenProcess(_SYNCHRONIZE, False, pid)
    if not handle:
        return True
    try:
        return _kernel32.WaitForSingleObject(handle, 0) != _WAIT_TIMEOUT
    finally:
        _kernel32.CloseHandle(handle)


def probe_job_tree() -> JobTreeProbe:
    """Create only synthetic parent/child processes, then terminate their Job."""

    _require_windows()
    parent: subprocess.Popen[str] | None = None
    job: WindowsJob | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="skillshift-job-probe-") as temp_name:
            root = Path(temp_name)
            parent_script = root / "synthetic_parent.py"
            parent_script.write_text(
                "from pathlib import Path\n"
                "import os, subprocess, sys, time\n"
                "root = Path(sys.argv[1])\n"
                "(root / 'parent_pid.txt').write_text(str(os.getpid()), encoding='utf-8')\n"
                "while not (root / 'start_child').exists(): time.sleep(0.02)\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
                "(root / 'child_pid.txt').write_text(str(child.pid), encoding='utf-8')\n"
                "while True: time.sleep(0.2)\n",
                encoding="utf-8",
            )
            parent = subprocess.Popen([sys.executable, "-I", str(parent_script), str(root)], text=True)
            _wait_for_path(root / "parent_pid.txt", timeout_seconds=3)
            job = WindowsJob()
            job.assign_process_handle(parent._handle)
            parent_in_job = job.contains_process_handle(parent._handle)
            (root / "start_child").write_text("start", encoding="utf-8")
            _wait_for_path(root / "child_pid.txt", timeout_seconds=3)
            child_pid = int((root / "child_pid.txt").read_text(encoding="utf-8"))
            child_in_job = job.contains_pid(child_pid)
            active_before = job.active_pids()
            job.terminate()
            parent.wait(timeout=3)
            deadline = time.monotonic() + 3
            while not _pid_has_exited(child_pid) and time.monotonic() < deadline:
                time.sleep(0.02)
            active_after = job.active_pids()
            child_exited = _pid_has_exited(child_pid)
            if not (parent_in_job and child_in_job and child_exited and not active_after):
                raise WindowsIsolationSpikeError("Job tree probe did not obtain complete termination evidence")
            return JobTreeProbe(
                state="PASS",
                parent_pid=parent.pid,
                child_pid=child_pid,
                parent_in_job=parent_in_job,
                child_in_job=child_in_job,
                active_pids_before_terminate=active_before,
                active_pids_after_terminate=active_after,
                parent_exited=parent.poll() is not None,
                child_exited=child_exited,
                detail="synthetic parent and standard CreateProcess child terminated through one Job Object",
            )
    except (OSError, subprocess.SubprocessError, WindowsIsolationSpikeError) as error:
        return JobTreeProbe(
            state="FAIL",
            parent_pid=parent.pid if parent else 0,
            child_pid=0,
            parent_in_job=False,
            child_in_job=False,
            active_pids_before_terminate=(),
            active_pids_after_terminate=(),
            parent_exited=parent.poll() is not None if parent else True,
            child_exited=False,
            detail=f"{type(error).__name__}: {error}",
        )
    finally:
        if job is not None:
            try:
                job.terminate()
            except WindowsIsolationSpikeError:
                pass
            try:
                job.close()
            except WindowsIsolationSpikeError:
                pass
        if parent is not None and parent.poll() is None:
            parent.kill()
            parent.wait(timeout=3)


def probe_zero_capability_profile() -> AppContainerProfileProbe:
    """Create and delete a one-off AppContainer profile without launching it."""

    _require_windows()
    profile_name = f"SkillShift.R0.Probe.{uuid4().hex}"
    sid = wintypes.LPVOID()
    create_result = _userenv.CreateAppContainerProfile(
        profile_name,
        "SkillShift R0 temporary probe",
        "Temporary zero-capability profile for a synthetic local test",
        None,
        0,
        ctypes.byref(sid),
    )
    if create_result != _S_OK:
        return AppContainerProfileProbe(
            state="BLOCKED",
            profile_name=profile_name,
            create_hresult=_hresult(create_result),
            delete_hresult=None,
            detail="profile creation failed; no policy or privilege escalation was attempted",
        )
    delete_result: int | None = None
    try:
        delete_result = _userenv.DeleteAppContainerProfile(profile_name)
        if delete_result != _S_OK:
            return AppContainerProfileProbe(
                state="FAIL",
                profile_name=profile_name,
                create_hresult=_hresult(create_result),
                delete_hresult=_hresult(delete_result),
                detail="profile was created but could not be deleted; no further probe is safe",
            )
        return AppContainerProfileProbe(
            state="PASS",
            profile_name=profile_name,
            create_hresult=_hresult(create_result),
            delete_hresult=_hresult(delete_result),
            detail="zero-capability profile lifecycle completed; no process was launched",
        )
    finally:
        if sid:
            _advapi32.FreeSid(sid)


def _token_is_appcontainer(process_handle: int) -> bool:
    token = wintypes.HANDLE()
    if not _advapi32.OpenProcessToken(wintypes.HANDLE(process_handle), _TOKEN_QUERY, ctypes.byref(token)):
        raise WindowsIsolationSpikeError(f"OpenProcessToken failed: {ctypes.WinError(ctypes.get_last_error())}")
    try:
        value = wintypes.DWORD()
        returned = wintypes.DWORD()
        if not _advapi32.GetTokenInformation(
            token,
            _TOKEN_IS_APPCONTAINER,
            ctypes.byref(value),
            ctypes.sizeof(value),
            ctypes.byref(returned),
        ):
            raise WindowsIsolationSpikeError(f"GetTokenInformation(TokenIsAppContainer) failed: {ctypes.WinError(ctypes.get_last_error())}")
        return bool(value.value)
    finally:
        _kernel32.CloseHandle(token)


def _sid_to_string(sid: wintypes.LPVOID) -> str:
    value = wintypes.LPWSTR()
    if not sid or not sid.value:
        raise WindowsIsolationSpikeError("AppContainer SID was empty")
    if not _advapi32.ConvertSidToStringSidW(wintypes.LPVOID(sid.value), ctypes.byref(value)):
        raise WindowsIsolationSpikeError(f"ConvertSidToStringSidW failed: {ctypes.WinError(ctypes.get_last_error())}")
    try:
        return str(value.value)
    finally:
        _kernel32.LocalFree(value)


def _grant_temporary_runner_acl(runner: Path, sid: wintypes.LPVOID) -> None:
    if not runner.is_dir() or runner.parent != runner.parents[0]:
        raise WindowsIsolationSpikeError("temporary runner must be a direct child of its dedicated temporary directory")
    result = subprocess.run(
        ["icacls", str(runner), "/grant:r", f"*{_sid_to_string(sid)}:(OI)(CI)RX", "/T", "/C"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if result.returncode != 0:
        raise WindowsIsolationSpikeError(f"temporary runner ACL command failed with exit code {result.returncode}")


def probe_appcontainer_python_launch(*, runner_directory: Path | None = None, code: str = "import sys; raise SystemExit(0)") -> AppContainerPythonProbe:
    """Launch only ``python -I -c`` inside a zero-capability AppContainer.

    No workspace is made available and no network action is attempted.  The
    process is created suspended, placed in a Job, inspected, then resumed.
    """

    _require_windows()
    profile_name = f"SkillShift.R0.PythonProbe.{uuid4().hex}"
    sid = wintypes.LPVOID()
    create_result = _userenv.CreateAppContainerProfile(
        profile_name,
        "SkillShift R0 Python probe",
        "Temporary zero-capability profile for a synthetic Python launch",
        None,
        0,
        ctypes.byref(sid),
    )
    if create_result != _S_OK:
        return AppContainerPythonProbe(
            state="BLOCKED",
            profile_name=profile_name,
            create_hresult=_hresult(create_result),
            delete_hresult=None,
            process_pid=0,
            token_is_appcontainer=False,
            process_in_job=False,
            exit_code=None,
            active_pids_after_exit=(),
            detail="profile creation failed; no policy or privilege escalation was attempted",
        )

    process_info = _PROCESS_INFORMATION()
    attribute_buffer: ctypes.Array[ctypes.c_char] | None = None
    attribute_list_initialized = False
    job: WindowsJob | None = None
    delete_result: int | None = None
    outcome: AppContainerPythonProbe | None = None
    observed_in_job = False
    observed_is_appcontainer = False
    observed_exit_code: int | None = None
    observed_active_pids: tuple[int, ...] = ()
    try:
        executable = Path(sys.executable)
        if runner_directory is not None:
            _grant_temporary_runner_acl(runner_directory, sid)
            executable = runner_directory / "python.exe"
            if not executable.is_file():
                raise WindowsIsolationSpikeError("temporary runner does not contain python.exe")
        attribute_size = ctypes.c_size_t()
        _kernel32.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(attribute_size))
        if ctypes.get_last_error() != 122:
            raise WindowsIsolationSpikeError(f"InitializeProcThreadAttributeList(size) failed: {ctypes.WinError(ctypes.get_last_error())}")
        attribute_buffer = ctypes.create_string_buffer(attribute_size.value)
        if not _kernel32.InitializeProcThreadAttributeList(attribute_buffer, 1, 0, ctypes.byref(attribute_size)):
            raise WindowsIsolationSpikeError(f"InitializeProcThreadAttributeList failed: {ctypes.WinError(ctypes.get_last_error())}")
        attribute_list_initialized = True
        capabilities = _SECURITY_CAPABILITIES(sid, None, 0, 0)
        if not _kernel32.UpdateProcThreadAttribute(
            attribute_buffer,
            0,
            _PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
            ctypes.byref(capabilities),
            ctypes.sizeof(capabilities),
            None,
            None,
        ):
            raise WindowsIsolationSpikeError(f"UpdateProcThreadAttribute(security capabilities) failed: {ctypes.WinError(ctypes.get_last_error())}")
        startup = _STARTUPINFOEXW()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.lpAttributeList = ctypes.cast(attribute_buffer, wintypes.LPVOID)
        command_line = ctypes.create_unicode_buffer(f'"{executable}" -I -c "{code}"')
        if not _kernel32.CreateProcessW(
            str(executable),
            command_line,
            None,
            None,
            False,
            _EXTENDED_STARTUPINFO_PRESENT | _CREATE_SUSPENDED,
            None,
            None,
            ctypes.byref(startup),
            ctypes.byref(process_info),
        ):
            raise WindowsIsolationSpikeError(f"CreateProcessW(AppContainer Python) failed: {ctypes.WinError(ctypes.get_last_error())}")
        job = WindowsJob()
        job.assign_process_handle(process_info.hProcess)
        observed_in_job = job.contains_process_handle(process_info.hProcess)
        observed_is_appcontainer = _token_is_appcontainer(process_info.hProcess)
        if _kernel32.ResumeThread(process_info.hThread) == _INVALID_DWORD:
            raise WindowsIsolationSpikeError(f"ResumeThread failed: {ctypes.WinError(ctypes.get_last_error())}")
        wait_result = _kernel32.WaitForSingleObject(process_info.hProcess, 5_000)
        if wait_result != _WAIT_OBJECT_0:
            raise WindowsIsolationSpikeError(f"AppContainer Python did not exit normally within 5 seconds (wait={wait_result})")
        exit_code = wintypes.DWORD()
        if not _kernel32.GetExitCodeProcess(process_info.hProcess, ctypes.byref(exit_code)):
            raise WindowsIsolationSpikeError(f"GetExitCodeProcess failed: {ctypes.WinError(ctypes.get_last_error())}")
        observed_exit_code = int(exit_code.value)
        observed_active_pids = job.active_pids()
        if not (observed_in_job and observed_is_appcontainer and observed_exit_code == 0 and not observed_active_pids):
            raise WindowsIsolationSpikeError(
                "AppContainer Python evidence incomplete "
                f"(token={observed_is_appcontainer}, job={observed_in_job}, "
                f"exit={observed_exit_code}, active={observed_active_pids})"
            )
        outcome = AppContainerPythonProbe(
            state="PASS",
            profile_name=profile_name,
            create_hresult=_hresult(create_result),
            delete_hresult=None,
            process_pid=int(process_info.dwProcessId),
            token_is_appcontainer=observed_is_appcontainer,
            process_in_job=observed_in_job,
            exit_code=observed_exit_code,
            active_pids_after_exit=observed_active_pids,
            detail="zero-capability AppContainer launched synthetic Python under one Job Object",
        )
    except WindowsIsolationSpikeError as error:
        outcome = AppContainerPythonProbe(
            state="FAIL",
            profile_name=profile_name,
            create_hresult=_hresult(create_result),
            delete_hresult=None,
            process_pid=int(process_info.dwProcessId),
            token_is_appcontainer=observed_is_appcontainer,
            process_in_job=observed_in_job,
            exit_code=observed_exit_code,
            active_pids_after_exit=observed_active_pids,
            detail=f"{type(error).__name__}: {error}",
        )
    finally:
        if job is not None:
            try:
                job.terminate()
            except WindowsIsolationSpikeError:
                pass
            try:
                job.close()
            except WindowsIsolationSpikeError:
                pass
        if process_info.hThread:
            _kernel32.CloseHandle(process_info.hThread)
        if process_info.hProcess:
            _kernel32.CloseHandle(process_info.hProcess)
        if attribute_buffer is not None and attribute_list_initialized:
            _kernel32.DeleteProcThreadAttributeList(attribute_buffer)
        delete_result = _userenv.DeleteAppContainerProfile(profile_name)
        if sid:
            _advapi32.FreeSid(sid)
    if delete_result != _S_OK:
        return AppContainerPythonProbe(
            state="FAIL",
            profile_name=profile_name,
            create_hresult=_hresult(create_result),
            delete_hresult=_hresult(delete_result),
            process_pid=outcome.process_pid if outcome else 0,
            token_is_appcontainer=False,
            process_in_job=False,
            exit_code=None,
            active_pids_after_exit=(),
            detail="profile cleanup failed; no further probe is safe",
        )
    assert outcome is not None
    return AppContainerPythonProbe(
        **{**asdict(outcome), "delete_hresult": _hresult(delete_result)}
    )


def probe_copied_runner(*, code: str = "import sys; raise SystemExit(0)") -> AppContainerPythonProbe:
    """Use only a temporary copy of the local Python runtime and clean it up."""

    _require_windows()
    with tempfile.TemporaryDirectory(prefix="skillshift-appcontainer-runner-") as temp_name:
        root = Path(temp_name)
        runner = root / "runner"
        shutil.copytree(Path(sys.executable).parent, runner)
        outcome = probe_appcontainer_python_launch(runner_directory=runner, code=code)
    return AppContainerPythonProbe(
        **{**asdict(outcome), "detail": f"{outcome.detail}; temporary runner directory removed"}
    )


def probe_zero_capability_network_denial() -> dict[str, object]:
    """Compare local-loopback baseline with a zero-capability AppContainer.

    The child exits 0 only if every TCP/UDP/bind/listen operation raises an
    OS error.  The host first proves the same actions work on IPv4 and IPv6.
    """

    _require_windows()
    servers: list[socket.socket] = []
    try:
        endpoints: list[tuple[int, str, int]] = []
        for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            tcp = socket.socket(family, socket.SOCK_STREAM)
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp.bind((host, 0))
            tcp.listen(2)
            port = tcp.getsockname()[1]
            baseline = socket.create_connection((host, port), timeout=1)
            accepted, _ = tcp.accept()
            baseline.close()
            accepted.close()
            udp = socket.socket(family, socket.SOCK_DGRAM)
            udp.bind((host, 0))
            udp_port = udp.getsockname()[1]
            baseline_udp = socket.socket(family, socket.SOCK_DGRAM)
            baseline_udp.sendto(b"b", (host, udp_port))
            udp.settimeout(1)
            udp.recvfrom(1)
            baseline_udp.close()
            bind_probe = socket.socket(family, socket.SOCK_STREAM)
            bind_probe.bind((host, 0))
            bind_probe.listen(1)
            bind_probe.close()
            servers.extend((tcp, udp))
            endpoints.extend(((family, host, port), (family, host, udp_port)))
        # Exit codes 81-86 identify the first action that succeeds.  A
        # SystemExit is not an OSError, so it cannot be mistaken for denial.
        codes = ((81, 82, 83), (84, 85, 86))
        fragments: list[str] = ["import socket,sys"]
        for ((family, host, port), (_, _, udp_port)), (tcp_code, udp_code, bind_code) in zip(
            zip(endpoints[::2], endpoints[1::2]), codes
        ):
            fragments.extend(
                (
                    f"try:\n s=socket.socket({family},socket.SOCK_STREAM);s.settimeout(.4);s.connect(('{host}',{port}));raise SystemExit({tcp_code})\nexcept OSError: pass",
                    f"try:\n u=socket.socket({family},socket.SOCK_DGRAM);u.sendto(b'x',('{host}',{udp_port}));raise SystemExit({udp_code})\nexcept OSError: pass",
                    f"try:\n b=socket.socket({family},socket.SOCK_STREAM);b.bind(('{host}',0));b.listen(1);raise SystemExit({bind_code})\nexcept OSError: pass",
                )
            )
        code = "\n".join(fragments) + "\nraise SystemExit(0)"
        outcome = probe_copied_runner(code=code)
        return {
            "state": "PASS" if outcome.state == "PASS" and outcome.exit_code == 0 else "FAIL",
            "baseline_ipv4_ipv6": "PASS",
            "appcontainer": asdict(outcome),
            "detail": "only local loopback baseline endpoints were used and closed",
        }
    except OSError as error:
        return {"state": "BLOCKED", "baseline_ipv4_ipv6": "INCOMPLETE", "detail": f"{type(error).__name__}: {error}"}
    finally:
        for server in servers:
            server.close()


def probe_as_json() -> dict[str, object]:
    """Run both bounded probes and return only non-sensitive evidence fields."""

    return {
        "schema_version": "r0-windows-isolation-launcher-spike/v1",
        "scope": "synthetic Windows primitive probes plus zero-capability AppContainer launches; copied runner ACL is temporary; no network or workspace ACL",
        "job_tree": asdict(probe_job_tree()),
        "appcontainer_profile": asdict(probe_zero_capability_profile()),
        "appcontainer_python": asdict(probe_appcontainer_python_launch()),
        "copied_runner": asdict(probe_copied_runner()),
        "network_denial": probe_zero_capability_network_denial(),
    }
