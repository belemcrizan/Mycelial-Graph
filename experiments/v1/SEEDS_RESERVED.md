# Reserved disjoint seed namespaces

Status: **contamination prevention only**. This file is not a preregistration, not a
frozen V1.5 protocol, and not permission to inspect confirmatory outcomes on
these blocks.

Existing V1 populations (do not reuse):

| Population | File | Values |
| --- | --- | --- |
| Development | `seeds.development.txt` | 1103, 2207, 3313, 4421, 5531 |
| Pilot | `seeds.pilot.txt` | 101003–103397 (20 seeds) |
| Confirmatory executed | `seeds.confirmatory.txt` | 700000–700096 |
| Confirmatory unused pool | `seeds.confirmatory.pool.txt` remainder | 700097–700499 |

Reserved for later programmes (disjoint integer blocks):

| Programme | Namespace | Permission |
| --- | --- | --- |
| Equalization calibration | 800000–800099 | Not a freeze gate until a protocol says so |
| Sanity / dynamic-range diagnostics | 810000–810099 | Not V1.5 confirmatory |
| V1.5 development | 820000–820099 | Implementation validation only after a V1.5 protocol exists |
| V1.5 pilot | 830000–830099 | Variance/sample-size only after protocol freeze |
| V1.5 confirmatory | 840000–840499 | Do not inspect until V1.5 is frozen and powered |

Do not tune on protected seeds.
Do not start V1.5 implementation before Paper A is submitted and a V1.5 protocol exists.
