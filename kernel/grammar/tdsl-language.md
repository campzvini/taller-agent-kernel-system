# TDSL Canonical Language Definition

¶ - Consolidate the living TDSL grammar into one production normative source without resetting its lineage.

document:
  id: tdsl.language@3
  version: 3
  status: proposed
  authority_basis: [@constitution/current @arch/tdsl-inheritance-ledger @research/source-global-rules @research/tdsl-1.1 @arch/product]
  scope: source_language, lexical_contract, structural_contract, templates, compatibility, error_contract
  excludes: parser_implementation, storage_implementation, host_API, empirical_claims

¶ 1 — Lineage and Communication

TDSL advances from Global TDSL v1 and TDSL 1.1. It preserves:

```text
principle:
  max_info_per_token
  min_invention
  semantics_over_syntax

channels:
  human_agent: natural_language
  agent_artifact: TDSL_source
  artifact_kernel: resolved_semantic_IR
  kernel_human: deterministic_publication
```

Free conversation is not required to use TDSL. TDSL applies when operational
meaning is authored, persisted, validated, referenced, routed, or transferred.

¶ 2 — Tracked Document Identity

A tracked standalone source begins:

```text
tdsl: <dialect>@<major>
schema_revision: sha256:<64_lower_hex>
id: @<namespace>/<identifier>
```

Common optional fields:

```text
version: <positive_integer>
status: <dialect_content_status>
purpose: <single_line_scalar>
```

Canonical order is `tdsl`, `schema_revision`, `id`, `version`, `status`,
`purpose`.

Rules:

- tracked source declares exact dialect major and schema revision;
- a transient governed response may omit values supplied by the authenticated
  request;
- external and inline values must match;
- filename, path, branch, timestamp, prose, or model inference cannot select a
  dialect or revision;
- organization, author, year, signature, slogan, and ornament are presentation
  profile data, not core identity.

¶ 3 — Encoding, Lines, and Indentation

```text
encoding: UTF-8
BOM: invalid
accepted_newlines: [LF CRLF]
canonical_newline: LF
lone_CR: invalid
final_newline: required
indent: 2_ASCII_spaces
tabs: invalid
trailing_whitespace: invalid
skipped_indent_level: invalid
```

CRLF is normalized to LF before canonical formatting and source digesting.
Blank lines have no semantic meaning. Canonical source uses at most one blank
line between top-level regions.

Line and column diagnostics count Unicode scalar values after newline
normalization. Byte offsets may be included as non-semantic diagnostics.

¶ 4 — Comments

A full-line comment begins with `#` after optional indentation.

```text
# source note
field:
  # local source note
  value: known
```

Inline comments are invalid. `#` is invalid inside a bare scalar and must be
quoted when literal. Inside quoted scalars and LN bodies it is content. Comments
are excluded from semantic IR and cannot supply fields, authority, conditions,
exceptions, or failure behavior.

¶ 5 — Keys, Identifiers, and References

```ebnf
letter = "A"…"Z" | "a"…"z" ;
lowercase_letter = "a"…"z" ;
digit = "0"…"9" ;
key_start = letter | digit | "_" ;
key_rest = letter | digit | "_" | "." | "-" ;
key = key_start, { key_rest } ;
namespace = lowercase_letter, { lowercase_letter | digit | "_" | "-" } ;
segment_start = letter | digit ;
segment_rest = letter | digit | "_" | "." | "~" | "-" ;
segment = segment_start, { segment_rest } ;
identifier = segment, { "/", segment } ;
```

Keys are case-sensitive. New keys should use lowercase snake_case. Repeated keys
are invalid unless the exact schema field declares ordered accumulation.

Base and part references are:

```text
@<namespace>/<identifier>
@<namespace>/<identifier>#<part_kind>/<part_id>
```

A reference imports identity only. Its namespace, target type, part kinds, and
cardinality are schema-defined. Reference resolution uses a finite immutable
snapshot. Required unresolved references refuse. Optional unresolved references
become `unknown` only where the field permits it.

¶ 6 — Properties, Blocks, and Labeled Blocks

```text
property:
  key: value

block:
  key:
    child: value

labeled_block:
  key label:
    child: value
```

Rules:

- one ASCII space follows `:` in a property;
- a block header ends at `:`;
- children are exactly one indentation level deeper;
- labeled blocks are valid only for schema-declared accumulated fields;
- labels are identifiers or quoted strings as declared by schema;
- source order is retained;
- visual nesting creates scope; the schema creates meaning.

A required accumulated field with `min_items: 0` represents a known empty set as:

```text
findings: []
```

It represents one or more items as:

```text
findings:
  finding F001:
    severity: material
```

An empty indented block is never used to represent zero items.

¶ 7 — Scalars and Value States

A bare scalar is one non-empty line without leading/trailing whitespace, tabs,
unescaped brackets, `->`, collection commas, `#`, or quote delimiters.

Double-quoted scalars support:

```text
\\
\"
\n
\r
\t
\uNNNN
```

Malformed escapes refuse. Decoded text must be valid Unicode. Quoting normally
has no semantic residue after schema typing, except that reserved state words
are recognized only when unquoted:

```text
unknown: explicit unavailable fact
empty: known absence of scalar or object value
"unknown": literal string
"empty": literal string
```

Omission is not written. A missing field means schema default or absence.
Collections use `[]` for known empty collection. A schema declares permitted
value states field by field.

Numbers:

```ebnf
integer = "0" | nonzero_digit, { digit } ;
decimal = [ "-" ], integer, [ ".", digit, { digit } ] ;
```

Leading plus signs, exponents, leading zeroes, and negative zero are invalid.
Semantic IR stores integer and decimal values as canonical decimal strings.

¶ 8 — Collections

Canonical form:

```text
refs: [@spec/current @plan/current]
```

Legacy compatible form:

```text
refs: [@spec/current, @plan/current]
```

Rules:

- whitespace and comma separators are accepted;
- one collection cannot mix separator styles;
- canonical formatting emits one space and no commas;
- quoted members may contain spaces;
- nested collections and inline source objects are invalid;
- ordering is preserved unless schema declares set semantics;
- duplicate members refuse unless explicitly allowed;
- set fields sort by canonical member bytes during normalization;
- a whole collection may be `unknown` as `refs: unknown`, not `[unknown]`,
  unless `unknown` is an allowed member value.

¶ 9 — Natural-Language Escape

```text
rationale ln: |
  Opaque natural language remains opaque.
```

The body begins one indentation level deeper than its owner. It continues
through body-indented lines and blank lines before a later body line. The first
nonblank dedented line ends the body. Relative indentation is preserved after
removing the body minimum. Newlines normalize to LF.

A body with no content represents `empty` only where permitted; otherwise it is
a syntax error. Parser and normalizer never derive normative fields from LN.

¶ 10 — Conditional Arrows

```text
conflict(arch) -> stop, report(op)
```

```ebnf
symbolic_call = identifier_token, [ "(", [ atom, { " ", atom } ], ")" ] ;
guarded_rule = symbolic_call, " -> ", symbolic_call,
               { ", ", symbolic_call } ;
```

Parentheses do not nest. Commas separate actions and cannot occur inside action
arguments. Conditions and actions are dialect vocabulary. Arrows represent
consequence; they do not execute effects or grant authority.

¶ 11 — Typed Templates

Templates are tracked `template@1` documents. Ordinary artifacts never contain
template directives.

Supported directives inside the template `body`:

```text
for <collection_placeholder> as <alias>:
  <output_nodes>

when <placeholder_or_alias_path>:
  <output_nodes>

when_empty <collection_or_block_list_placeholder>:
  <output_nodes>
```

`when` emits when a value is present and non-empty. `when_empty` emits only when
a present typed collection or block list contains zero items. Optional omission
causes neither branch unless the template explicitly models a default.

Placeholder forms:

```text
{name}: scalar, complete typed field value, reference component, or LN segment
{*name}: zero-or-more collection members
{#name}: complete schema-validated child fields of one object
{alias.field}: repeated-item scalar, value state, or LN value
{*alias.field}: repeated-item collection splice
```

Rules:

- every placeholder declares kind, type, and requiredness;
- block-list and collection placeholders may additionally declare item type and
  collection semantics;
- instantiation is typed and context-aware, never raw string substitution;
- `for` preserves ordered input and canonicalizes set input;
- `when_empty` is the canonical way to emit `container: []` for a required
  zero-item accumulated field;
- object splices emit only fields declared by the object contract;
- expansion is single-pass and non-recursive;
- instantiated output contains no directives or placeholders;
- output is reparsed and validated as ordinary source under its exact output
  schema revision.

The complete contract is `docs/architecture/tdsl-template-contract.md`.

¶ 12 — Canonical Source Formatting

Canonical source:

- uses UTF-8 without BOM and LF;
- ends with one newline;
- uses two spaces per level;
- has no trailing whitespace;
- uses common-header order;
- follows schema field order;
- uses bare scalars when safe;
- quotes reserved words when literal;
- emits whitespace-separated collections;
- emits `condition -> action, action`;
- preserves LN text after newline normalization;
- may preserve full-line comments without semantics.

Formatting cannot change semantic IR.

¶ 13 — Dialects, Types, and Schema Locks

Dialect identity is `<name>@<major>`. Exact schema revisions are SHA-256 digests
of canonical schema JSON registered in:

```text
docs/architecture/tdsl/schemas/registry.json
```

Named types resolve through:

```text
docs/architecture/tdsl/schemas/core-types@1.schema.json
```

Compatibility:

- removing or renaming a field is breaking;
- adding a required field is breaking;
- changing type, value state, reference target, invariant, authority, condition,
  action, or an operational default is breaking;
- removing or changing an existing named type is breaking;
- adding an optional field or unused named type is compatible;
- breaking changes increment dialect major;
- compatible revisions retain major and receive a new exact digest;
- tracked artifacts remain bound to their exact revision;
- nearest/current/prose fallback is forbidden;
- migrations are explicit mappings, never silent reinterpretation.

¶ 14 — Deterministic Errors

Error object:

```text
error:
  code
  category
  message
  document_id?
  location?
    line
    column
    unit: Unicode_scalar_value
  path?
```

Phase precedence:

```text
1 encoding_and_lexical
2 syntax
3 template
4 schema_binding_and_typecheck
5 reference_resolution
6 normalization
7 artifact_invariants
8 workflow_and_authority
9 publication
```

The runtime stops after the first failing phase and returns all independent
errors from that phase ordered by source offset and then code. Parser recovery
does not create downstream errors.

Stable codes include:

```text
TDSL-E101 invalid_UTF8
TDSL-E102 BOM_forbidden
TDSL-E103 lone_CR
TDSL-E104 tab
TDSL-E105 invalid_indent
TDSL-E106 trailing_whitespace
TDSL-E107 invalid_escape
TDSL-E201 malformed_property_or_block
TDSL-E202 malformed_collection
TDSL-E203 mixed_collection_separators
TDSL-E204 malformed_LN
TDSL-E205 malformed_arrow
TDSL-E206 invalid_empty_accumulated_representation
TDSL-E301 unresolved_schema
TDSL-E302 schema_revision_mismatch
TDSL-E303 unknown_field
TDSL-E304 invalid_type
TDSL-E305 required_field_missing
TDSL-E401 malformed_reference
TDSL-E402 disallowed_reference
TDSL-E403 unresolved_required_reference
TDSL-E501 undeclared_placeholder
TDSL-E502 missing_required_placeholder
TDSL-E503 invalid_template_context
TDSL-E504 unresolved_template_directive
TDSL-E505 placeholder_type_mismatch
TDSL-E506 output_schema_mismatch
TDSL-E601 non_deterministic_normalization
TDSL-E701 incompatible_dialect
TDSL-E801 publication_failure
```

Messages may improve without changing code meaning. Warnings never repair
invalid source.

¶ 15 — Claims

This definition establishes normative behavior. It does not claim token savings,
cross-model stability, benchmark superiority, or commercial performance.
