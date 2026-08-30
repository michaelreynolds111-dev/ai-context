#!/usr/bin/env python3
"""path_canonicalize.py — Shared canonical path model for Computer File Steward v1.0.1.

Correction A: ONE shared canonicalisation contract used by inventory, validation,
report generation, and tests.

Supported input forms (all normalised safely):
    C:\\Users\\micha\\example            Windows drive (backslashes)
    C:/Users/micha/example             Windows drive (forward slashes)
    \\\\wsl.localhost\\Ubuntu-24.04\\home\\michael\\example   WSL via wsl.localhost UNC
    \\\\wsl$\\Ubuntu-24.04\\home\\michael\\example            WSL via wsl$ UNC
    /home/michael/example              WSL-native

Design rules (from task section 4.2):
  - Reject absent/empty targets.
  - Resolve "." and ".." lexically and safely (never via filesystem).
  - Preserve root boundaries (never collapse ".." above a root).
  - Normalise separator differences (\\ -> /).
  - Treat Windows drive letters case-insensitively for *comparison*, preserve
    case for *display*.
  - Distinguish filesystem identity (identity key) from display path.
  - Reject malformed drive-relative forms such as "C:folder".
  - Recognise UNC roots and approved WSL UNC mappings.
  - Prevent prefix confusion (C:\\safe must not contain C:\\safety) by comparing
    whole components, not raw string prefixes.
  - Never resolve or traverse reparse points merely to normalise.
  - Fail closed when equivalence cannot be proven.

Equivalence stance: Windows "C:\\..." and WSL "/home/..." representations are NOT
assumed equivalent. Only the explicit WSL-mapping relationships are honoured:
    \\\\wsl.localhost\\Ubuntu-24.04\\home\\michael\\X  ==  /home/michael/X
    \\\\wsl$\\Ubuntu-24.04\\home\\michael\\X        ==  /home/michael/X
    \\\\wsl.localhost\\Ubuntu-24.04\\mnt\\c\\X      ==  C:\\X
Everything else that cannot be proven equivalent is treated as distinct (fail
closed): such paths are never reported as contained/equal.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

WSL_DISTRO = "Ubuntu-24.04"

_UNC_WSL_HOST = re.compile(r"^//wsl\.localhost/(?P<distro>[^/]+)/(?P<rest>.*)$", re.IGNORECASE)
_UNC_WSLCENT = re.compile(r"^//wsl\$(?:/(?P<distro>[^/]+))?/(?P<rest>.*)$", re.IGNORECASE)
_DRIVE = re.compile(r"^(?P<letter>[A-Za-z]):/(?P<rest>.*)$")
_DRIVE_RELATIVE_MALFORMED = re.compile(r"^(?P<letter>[A-Za-z]):(?![/\\]).*$")
_WSL_MNT = re.compile(r"^mnt/(?P<letter>[A-Za-z])/(?P<rest>.*)$")


@dataclass(frozen=True)
class PathSpec:
    display: str
    style: str
    identity: Optional[str]
    is_root_boundary: bool = False
    error: Optional[str] = None
    input_path: str = ""

    @property
    def ok(self) -> bool:
        return self.error is None and self.identity is not None


def _lex_resolve(parts, root_path, style):
    """Resolve . and .. lexically, preserving the root. Returns (identity, display)
    or None on escape-above-root."""
    out = []
    for part in parts:
        if part in ("", "."):
            continue
        if part == "..":
            if out:
                out.pop()
            else:
                return None
        else:
            out.append(part)
    if not out:
        return (style + ":" + root_path, "/")
    return (style + ":" + root_path + "/".join(out), "/" + "/".join(out))


def _canon_wsl_native(p):
    """p like '/home/michael/example' or 'home/...'."""
    body = p.lstrip("/")
    if body.startswith("mnt/"):
        m = _WSL_MNT.match(body)
        if m:
            letter = m.group("letter").upper()
            rest = m.group("rest")
            return _canon_windows_drive(letter + ":/" + rest)
    parts = [seg for seg in body.split("/") if seg not in ("", ".")]
    res = _lex_resolve(parts, "/", "wsl")
    if res is None:
        return PathSpec(display=p, style="wsl_native", identity=None, error="escape above root", input_path=p)
    ident, disp = res
    return PathSpec(display=disp, style="wsl_native", identity=ident,
                    is_root_boundary=(not parts), input_path=p)


def _canon_windows_drive(p):
    m = _DRIVE.match(p)
    if not m:
        return PathSpec(display=p, style="windows", identity=None, error="unparsable drive path", input_path=p)
    letter = m.group("letter").upper()
    rest = m.group("rest")
    parts = [seg for seg in rest.split("/") if seg not in ("", ".")]
    res = _lex_resolve(parts, letter + ":/", "win")
    if res is None:
        return PathSpec(display=p, style="windows", identity=None, error="escape above drive root", input_path=p)
    ident, disp = res
    disp = letter + ":" + disp
    return PathSpec(display=disp, style="windows", identity=ident,
                    is_root_boundary=(not parts), input_path=p)


def _canon_wsl_unc(p, distro, rest):
    if distro != WSL_DISTRO:
        return PathSpec(display=p, style="wsl_unc", identity=None,
                        error="unmapped WSL distro '" + distro + "'", input_path=p)
    inner = _canon_wsl_native(rest)
    if inner.ok:
        return PathSpec(display="/" + rest, style="wsl_unc", identity=inner.identity,
                        is_root_boundary=inner.is_root_boundary, input_path=p)
    return PathSpec(display=p, style="wsl_unc", identity=None, error="unresolvable WSL UNC", input_path=p)


def canonicalize_path(path):
    if path is None or not str(path).strip():
        return PathSpec(display="", style="unknown", identity=None, error="empty target", input_path=str(path))
    raw = str(path)
    p = raw.strip().replace("\\", "/")
    # Malformed drive-relative "C:folder"
    if _DRIVE_RELATIVE_MALFORMED.match(p):
        return PathSpec(display=raw, style="unknown", identity=None, error="malformed drive-relative path", input_path=raw)
    # WSL UNC
    m = _UNC_WSL_HOST.match(p)
    if m:
        return _canon_wsl_unc(raw, m.group("distro"), m.group("rest"))
    m = _UNC_WSLCENT.match(p)
    if m:
        return _canon_wsl_unc(raw, m.group("distro") or WSL_DISTRO, m.group("rest"))
    # Windows drive
    m = _DRIVE.match(p)
    if m:
        return _canon_windows_drive(p)
    # WSL native (single leading slash)
    if p.startswith("/") and not p.startswith("//"):
        return _canon_wsl_native(p)
    # generic UNC (double leading slash) we cannot map
    if p.startswith("//"):
        return PathSpec(display=p, style="unknown", identity=None, error="unmappable UNC root", input_path=raw)
    # relative
    return PathSpec(display=p, style="unknown", identity=None, error="relative path not accepted", input_path=raw)


def paths_equivalent(a, b):
    pa = canonicalize_path(a)
    pb = canonicalize_path(b)
    if (not pa.ok) or (not pb.ok):
        return None
    return pa.identity == pb.identity


def target_contains(target, candidate):
    pt = canonicalize_path(target)
    pc = canonicalize_path(candidate)
    if (not pt.ok) or (not pc.ok):
        return None
    if pt.identity == pc.identity:
        return True
    if pt.identity is None or pc.identity is None:
        return None
    base = pt.identity.rstrip("/")
    if pc.identity == base + "/":
        return True
    if pc.identity.startswith(base + "/"):
        return True
    return False
