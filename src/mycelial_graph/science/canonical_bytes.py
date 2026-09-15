"""Line-ending canonicalization for new scientific hashes.

Historically frozen hashes (seed file, sealed confirmatory artifacts) are hashes
of the stored bytes and MUST NOT be recomputed after newline rewriting. New
text hashes that this repository declares as canonical use LF newlines.
"""

from __future__ import annotations

import hashlib


def normalize_newlines(data: bytes) -> bytes:
    """Map CR LF and bare CR to LF without altering other bytes."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_raw(data: bytes) -> str:
    """Hash of stored bytes. Use for historically frozen artifacts."""
    return hashlib.sha256(data).hexdigest()


def sha256_lf_text(data: bytes) -> str:
    """Hash after LF canonicalization. Use only for newly declared text hashes."""
    return hashlib.sha256(normalize_newlines(data)).hexdigest()
