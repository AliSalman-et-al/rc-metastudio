# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""OS-supplied PE imports accepted by the Windows packaging stages."""

R_KIT_SYSTEM_DLLS = frozenset({
    "advapi32.dll",
    "bcrypt.dll",
    "cfgmgr32.dll",
    "comctl32.dll",
    "comdlg32.dll",
    "crypt32.dll",
    "cryptbase.dll",
    "dnsapi.dll",
    "dwmapi.dll",
    "gdi32.dll",
    "imm32.dll",
    "iphlpapi.dll",
    "kernel32.dll",
    "msvcrt.dll",
    "ncrypt.dll",
    "netapi32.dll",
    "normaliz.dll",
    "ntdll.dll",
    "ole32.dll",
    "oleaut32.dll",
    "powrprof.dll",
    "propsys.dll",
    "psapi.dll",
    "rpcrt4.dll",
    "secur32.dll",
    "setupapi.dll",
    "shell32.dll",
    "shlwapi.dll",
    "ucrtbase.dll",
    "user32.dll",
    "userenv.dll",
    "version.dll",
    "winhttp.dll",
    "wininet.dll",
    "winmm.dll",
    "wldap32.dll",
    "ws2_32.dll",
})

APP_SYSTEM_DLLS = frozenset({
    "authz.dll",
    "bcryptprimitives.dll",
    "credui.dll",
    "d2d1.dll",
    "d3d11.dll",
    "d3d12.dll",
    "d3d9.dll",
    "dbghelp.dll",
    "dwrite.dll",
    "dxgi.dll",
    "gdiplus.dll",
    "icuuc.dll",
    "imagehlp.dll",
    "mpr.dll",
    "mscms.dll",
    "msimg32.dll",
    "pdh.dll",
    "uiautomationcore.dll",
    "usp10.dll",
    "uxtheme.dll",
    "wtsapi32.dll",
})


def is_system_import(name: str, accepted_dlls: frozenset[str]) -> bool:
    normalized = name.casefold()
    return normalized in accepted_dlls or normalized.startswith(("api-ms-win-", "ext-ms-win-"))
