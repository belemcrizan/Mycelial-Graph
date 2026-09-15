"""Line-ending and SHA-256 policy for scientific artifacts.

Hash semantics (do not mix them):

A. raw byte identity
   SHA-256 of stored bytes with no transformation. Use for PNG/binary artifacts,
   Git blobs, and any hash that must detect every byte change.

B. canonical textual identity
   SHA-256 after mapping CRLF and lone CR to LF. Use when the scientific
   contract is the text, not a particular newline convention.

C. source-tree identity
   ``source_digest``: ordered ``src/**/*.py`` relative paths plus raw file bytes.
   This identifies the current implementation tree, not a historical execution.

D. frozen input identity
   For confirmatory seeds the historical freeze recorded SHA-256
   ``8ef4c6b0…``. Independent reconstruction shows that digest is the CRLF
   byte representation of the seed list. Git stores the same list as LF
   (content SHA-256 ``2198ac5f…``). LF → CRLF reconstructs the frozen digest
   exactly. The seed *values* are identical. Do not change the frozen hash.

E. binary artifact identity
   Same as A. Binary files are never EOL-normalized.

F. parsed semantic identity
   ``config_digest`` / ``config_hash`` of the parsed configuration. YAML
   newlines do not affect this hash.

Historical V1 text seals captured CRLF bytes. The repository stores LF. Those
two representations are not "the hashes were wrong"; they are two byte
encodings of the same canonical text. Compatibility is explicit, scoped to
known artifacts, and reconstruction-checked. Arbitrary text mutation must fail.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final

# Kept as a public alias: existing tests import this name.
def normalize_newlines(data: bytes) -> bytes:
    """Map CRLF and bare CR to LF without altering other bytes."""
    return canonicalize_text_bytes(data)


def canonicalize_text_bytes(data: bytes) -> bytes:
    """Repository/canonical text representation: LF newlines.

    Independent of ``os.linesep``. Does not belong on binary files.
    """
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def lf_to_crlf(data: bytes) -> bytes:
    """Deterministic historical reconstruction: canonical LF -> CRLF.

    Input is canonicalized first so mixed endings cannot smuggle extra bytes.
    """
    return canonicalize_text_bytes(data).replace(b"\n", b"\r\n")


def contains_non_lf_newlines(data: bytes) -> bool:
    return b"\r" in data


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_raw(data: bytes) -> str:
    """Hash of stored bytes. Use for historically frozen raw identities."""
    return sha256_bytes(data)


def sha256_lf_text(data: bytes) -> str:
    """Hash after LF canonicalization. Alias of canonical textual identity."""
    return sha256_bytes(canonicalize_text_bytes(data))


def sha256_canonical_text(data: bytes) -> str:
    return sha256_lf_text(data)


def sha256_raw_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_canonical_text_file(path: Path) -> str:
    return sha256_canonical_text(path.read_bytes())


def frozen_text_input_sha256(path: Path) -> str:
    """Canonical LF SHA-256 of a text input. Not always equal to a historical CRLF seal."""
    return sha256_canonical_text_file(path)


def historical_newline_hashes(data: bytes) -> dict[str, str]:
    """Raw, canonical LF, and reconstructed CRLF hashes of the same text."""
    canonical = canonicalize_text_bytes(data)
    return {
        "raw": sha256_raw(data),
        "canonical_lf": sha256_bytes(canonical),
        "reconstructed_crlf": sha256_bytes(lf_to_crlf(canonical)),
    }


def historical_text_identity_matches(data: bytes, expected_sha256: str) -> bool:
    """True iff expected is raw, canonical LF, or reconstructed CRLF of data.

    Only newline encoding may differ. Any other mutation fails.
    """
    return expected_sha256 in historical_newline_hashes(data).values()


def verify_frozen_seed_identity(path: Path, expected_sha256: str | None = None) -> SealCheck:
    """Verify the confirmatory seed file against the historical freeze hash."""
    expected = expected_sha256 if expected_sha256 is not None else FROZEN_SEED_SHA256
    raw = path.read_bytes()
    hashes = historical_newline_hashes(raw)
    if hashes["raw"] == expected:
        identity = SealIdentity.EXACT
        message = "seeds: exact raw-byte match to frozen SHA-256"
    elif hashes["reconstructed_crlf"] == expected or hashes["canonical_lf"] == expected:
        identity = SealIdentity.HISTORICAL_EOL_EQUIVALENT
        message = (
            "seeds: historical freeze SHA-256 verified from newline-equivalent "
            "canonical seed content (CRLF-sealed identity, LF repository blob)"
        )
    else:
        identity = SealIdentity.MISMATCH
        message = (
            f"seeds: frozen SHA-256 {expected} matches neither raw "
            f"{hashes['raw']}, canonical LF {hashes['canonical_lf']}, nor "
            f"reconstructed CRLF {hashes['reconstructed_crlf']}"
        )
    return SealCheck(
        artifact=str(path),
        identity=identity,
        expected_sha256=expected,
        repository_raw_sha256=hashes["raw"],
        canonical_text_sha256=hashes["canonical_lf"],
        reconstructed_crlf_sha256=hashes["reconstructed_crlf"],
        message=message,
    )


class SealIdentity(str, Enum):
    EXACT = "EXACT"
    HISTORICAL_EOL_EQUIVALENT = "HISTORICAL_EOL_EQUIVALENT"
    MISMATCH = "MISMATCH"


# Only these historical confirmatory text artifacts may use EOL reconstruction.
# Keys match CONFIRMATORY_EVIDENCE.json sealed_artifact_sha256.
HISTORICAL_TEXT_SEAL_ARTIFACTS: Final[frozenset[str]] = frozenset(
    {
        "REPORT.md",
        "manifest.json",
        "processed/analysis.json",
    }
)

HISTORICAL_BINARY_SEAL_ARTIFACTS: Final[frozenset[str]] = frozenset(
    {
        "figures/recovery_by_rho.png",
        "figures/regret_by_rho.png",
    }
)

HISTORICAL_CRLF_SEAL_SHA256: Final[dict[str, str]] = {
    "REPORT.md": "a000e49f91d262490530e0dd92001d88f4dfca399c127de957853ad4a3ef0a18",
    "manifest.json": "242b58b39a5c000259c205aed9037bedf030d631b1cc3ab5466ab35736fba30a",
    "processed/analysis.json": "cd25c72c530440a888b8f52129f353ab24fa5c1a0da0f6fa95a91dc85e4ce892",
}

FROZEN_SEED_SHA256: Final[str] = "8ef4c6b0dc481fea70054b6d7cbc9ecc2663f63b4523f3f55bb374a0339ee00c"
# Repository Git blob of seeds.confirmatory.txt is LF; SHA-256 of those blob bytes:
FROZEN_SEED_GIT_BLOB_LF_SHA256: Final[str] = "2198ac5f8f2bf323ed409adf1f97c0f16b0f023a3dffd56f308856c9943fb67e"
FROZEN_CONFIG_HASH: Final[str] = "5d7e92d2ec2805418f2b07e641188814282d544de55eb8c1461f4400b025452a"
PRIMARY_ESTIMATE: Final[float] = 0.42112797022616655
ONE_SIDED_UPPER_BOUND: Final[float] = 0.7213788509020655
CONFIRMATORY_N: Final[int] = 97
CONFIRMATORY_RHO_COUNT: Final[int] = 5
CONFIRMATORY_METHOD_COUNT: Final[int] = 4
# 97 paired scenarios × 5 rho values = 485 scientific jobs (one job per seed×rho).
CONFIRMATORY_SCIENTIFIC_JOBS: Final[int] = CONFIRMATORY_N * CONFIRMATORY_RHO_COUNT
# 485 jobs × 4 methods = 1940 method-level trials. Not interchangeable with job count.
CONFIRMATORY_METHOD_TRIALS: Final[int] = CONFIRMATORY_SCIENTIFIC_JOBS * CONFIRMATORY_METHOD_COUNT
PROTOCOL_VERSION: Final[str] = "MG-EXP-V1"
RESULT_STATE: Final[str] = "REFUTED"


@dataclass(frozen=True)
class SealCheck:
    artifact: str
    identity: SealIdentity
    expected_sha256: str
    repository_raw_sha256: str
    canonical_text_sha256: str | None
    reconstructed_crlf_sha256: str | None
    message: str

    @property
    def ok(self) -> bool:
        return self.identity is not SealIdentity.MISMATCH


def verify_raw_bytes_seal(path: Path, expected_sha256: str, artifact: str) -> SealCheck:
    """Exact raw-byte identity. Never EOL-normalizes."""
    raw_hash = sha256_raw_file(path)
    if raw_hash == expected_sha256:
        identity = SealIdentity.EXACT
        message = f"{artifact}: exact raw-byte match"
    else:
        identity = SealIdentity.MISMATCH
        message = (
            f"{artifact}: raw SHA-256 mismatch "
            f"(expected {expected_sha256}, observed {raw_hash})"
        )
    return SealCheck(
        artifact=artifact,
        identity=identity,
        expected_sha256=expected_sha256,
        repository_raw_sha256=raw_hash,
        canonical_text_sha256=None,
        reconstructed_crlf_sha256=None,
        message=message,
    )


def verify_historical_text_seal(path: Path, expected_sha256: str, artifact: str) -> SealCheck:
    """Verify a known historical text seal, allowing only LF<->CRLF reconstruction.

    Passes when:
    * repository bytes hash to the stored historical SHA-256 (EXACT); or
    * canonical LF -> CRLF reconstructs the historical SHA-256 exactly
      (HISTORICAL_EOL_EQUIVALENT).

    Any other mutation is MISMATCH. This is not "if text: pass".
    """
    if artifact not in HISTORICAL_TEXT_SEAL_ARTIFACTS:
        raise ValueError(
            f"Historical EOL compatibility is not defined for {artifact!r}. "
            "Only the three historically sealed V1 text artifacts may use it."
        )
    raw = path.read_bytes()
    raw_hash = sha256_raw(raw)
    canonical = canonicalize_text_bytes(raw)
    canonical_hash = sha256_bytes(canonical)
    reconstructed = lf_to_crlf(canonical)
    reconstructed_hash = sha256_bytes(reconstructed)
    if raw_hash == expected_sha256:
        return SealCheck(
            artifact=artifact,
            identity=SealIdentity.EXACT,
            expected_sha256=expected_sha256,
            repository_raw_sha256=raw_hash,
            canonical_text_sha256=canonical_hash,
            reconstructed_crlf_sha256=reconstructed_hash,
            message=f"{artifact}: exact raw-byte match",
        )
    content_preserved = canonicalize_text_bytes(reconstructed) == canonical
    if reconstructed_hash == expected_sha256 and content_preserved:
        return SealCheck(
            artifact=artifact,
            identity=SealIdentity.HISTORICAL_EOL_EQUIVALENT,
            expected_sha256=expected_sha256,
            repository_raw_sha256=raw_hash,
            canonical_text_sha256=canonical_hash,
            reconstructed_crlf_sha256=reconstructed_hash,
            message=(
                f"{artifact}: historical CRLF seal verified from canonical LF content"
            ),
        )
    return SealCheck(
        artifact=artifact,
        identity=SealIdentity.MISMATCH,
        expected_sha256=expected_sha256,
        repository_raw_sha256=raw_hash,
        canonical_text_sha256=canonical_hash,
        reconstructed_crlf_sha256=reconstructed_hash,
        message=(
            f"{artifact}: neither raw bytes nor LF->CRLF reconstruction match "
            f"historical SHA-256 {expected_sha256} (raw {raw_hash}, "
            f"reconstructed {reconstructed_hash})"
        ),
    )


def human_seal_line(check: SealCheck) -> str:
    if check.identity is SealIdentity.EXACT:
        return f"[PASS] seal:{check.artifact}: exact raw-byte match"
    if check.identity is SealIdentity.HISTORICAL_EOL_EQUIVALENT:
        return (
            f"[PASS] seal:{check.artifact}: historical CRLF seal verified "
            "from canonical LF content"
        )
    return f"[FAIL] seal:{check.artifact}: {check.message}"
