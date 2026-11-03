---
name: provenance
description: Record incorporated-source origin, attribution and functional versus documentary adaptations.
---

¶ - Preserve incorporated-source lineage without another governance system.

skill:
  id: @skill/provenance
  role: optional_session_work

¶ 1 — Establish Origin

origin:
  required: [source_location immutable_revision_or_unknown license attribution destination_refs]
  evidence: targeted_upstream_source_and_license
  unknown: literal_unknown_never_invented
rule: original_sources_untouched_without_explicit_instruction

¶ 2 — Classify Adaptations

adaptations:
  functional: behavior_interfaces_build_or_dependency_changes
  documentary: headers_sections_context_comments_navigation
  verification: functional_validation_or_comment_guard_as_applicable
rule: preserve_authorship_license_and_notices
rule: material_choices_in_decisions_journal_with_evidence

¶ 3 — Report

report:
  compact: origin_destination_and_adaptation_classes
  detail: specific_diffs_and_evidence_on_request
ban: equivalence_or_license_compliance_claim_without_evidence
