"""Report-level claim containment for MG-EXP-V1.

MG-EXP-V1 tests exactly two frozen hypotheses: hierarchical versus edge-only at
``rho=0.50`` on restricted recovery time, and a ``rho=0`` non-inferiority safety gate.
No V1 artifact may assert anything beyond that boundary. This module scans generated
report text for assertive language outside the boundary and refuses to emit it.

A segment is exempt when it carries an explicit negation cue, so that documented
limitations such as "not powered to establish a crossover" remain sayable.

This is a containment mechanism for text this repository generates. It is not a general
natural-language contradiction detector, and it is not applied to hand-written prose.
"""

from __future__ import annotations

import re
from typing import Any

FORBIDDEN_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        "V1-CROSSOVER-EXISTENCE",
        r"\b(identif|establish|discover|detect|confirm|prov|observ)\w*\b[^|\n]{0,60}\bcrossover\b",
        "V1 is not designed or powered to establish the existence of a crossover.",
    ),
    (
        "V1-CROSSOVER-LOCATION",
        r"\bcrossover\b[^|\n]{0,60}\b(occurs?|lies|located|estimated|found|equals)\b"
        r"|\brho\s*\*\s*(=|==|is|≈)\s*-?\d",
        "V1 cannot locate a crossover rho*.",
    ),
    (
        "V1-PHASE-TRANSITION",
        r"\bphase[- ]transition\b",
        "A phase transition in rho is outside the frozen V1 design.",
    ),
    (
        "V1-RHO-GENERALISATION",
        r"\b(for|at|across) (all|every) rho\b|\ball[- ]rho\b|\bmonotonic\w*\b|\buniversal\w*\b",
        "V1 measures two frozen rho points; it cannot generalise across the rho grid.",
    ),
    (
        "V1-PRODUCTION",
        r"\bproduction[- ](read(y|iness)|grade|superiority)\b|\bready for production\b",
        "No production-readiness claim is supported by simulated evidence.",
    ),
    (
        "V1-EXTERNAL-VALIDITY",
        r"\breal[- ](world|provider)\b|\bgeneralis\w+ to\b|\bgeneraliz\w+ to\b",
        "V1 is synthetic; external validity requires a separate protocol and real data.",
    ),
    (
        "V1-CAUSAL",
        r"\bcausal\w*\b|\bcauses\b|\bfault localisation\b|\bfault localization\b",
        "The execution DAG is not a causal DAG; causal language requires an explicit SCM.",
    ),
    (
        "V1-THEORY",
        r"\btheorem\b|\bprov(es|en|ed)\b|\bregret bound\b|\bsample[- ]complexity\b|\bguarantee[sd]?\b",
        "V1 produces empirical evidence, not theoretical results.",
    ),
    (
        "V1-INDEPENDENT-REPRODUCTION",
        r"\bindependent(ly)? (reproduc|replicat)\w+\b|\bthird[- ]party reproduc\w+\b",
        "Reproduction inside this repository is internal/automated, never independent.",
    ),
    (
        "V1-PILOT-PROMOTION",
        r"\bpilot\b[^|\n]{0,40}\bconfirmatory (evidence|result|support)\b",
        "Pilot evidence can never be promoted to confirmatory evidence.",
    ),
)

NEGATION_CUES: tuple[str, ...] = (
    "not ",
    "n't",
    "no ",
    "never",
    "cannot",
    "can not",
    "without",
    "unsupported",
    "forbidden",
    "prohibit",
    "exclud",
    "absent",
    "neither",
    " nor ",
    "lacks",
    "outside",
    "beyond",
)

_SEGMENT_SPLIT = re.compile(r"[.!?;\n|]+")


class ClaimContainmentError(RuntimeError):
    """Raised when generated text asserts a claim outside the V1 boundary."""


def _is_negated(segment: str) -> bool:
    lowered = segment.lower()
    return any(cue in lowered for cue in NEGATION_CUES)


def find_claim_violations(text: str) -> list[dict[str, Any]]:
    """Return assertive out-of-boundary claims found in ``text``."""
    violations: list[dict[str, Any]] = []
    for segment in _SEGMENT_SPLIT.split(text):
        stripped = segment.strip()
        if not stripped or _is_negated(stripped):
            continue
        for identifier, pattern, reason in FORBIDDEN_PATTERNS:
            match = re.search(pattern, stripped, flags=re.IGNORECASE)
            if match:
                violations.append(
                    {
                        "id": identifier,
                        "matched_text": match.group(0),
                        "segment": stripped[:200],
                        "reason": reason,
                    }
                )
    return violations


def assert_claim_containment(text: str, source: str) -> None:
    """Raise if ``text`` asserts anything outside the frozen V1 claim boundary."""
    violations = find_claim_violations(text)
    if violations:
        detail = "\n".join(
            f" - [{item['id']}] {item['matched_text']!r} in {item['segment']!r}: {item['reason']}"
            for item in violations
        )
        raise ClaimContainmentError(
            f"Claim containment failed for {source}. "
            f"MG-EXP-V1 evidence cannot support the following language:\n{detail}"
        )
