# Provenance

Every immutable external dataset must eventually record:

```text
source
source_version
retrieved_at_utc
license
terms_of_use
transformations
canonical_hash
exclusions
contamination_caveats
parent_hashes (if derived)
```

Internal provenance fields on adapted records:

- `source_id`, `source_version`, `license_state`, `record_sha256`
- incidents additionally carry `annotation_role = external_incident_annotation_not_causal_truth`

Derived datasets must not overwrite raw parents. Create a new versioned artifact.

No external raw files are present at this commit. Hash fields apply to fixtures and to future local caches outside git.
