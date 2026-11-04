# Install — instructions for the installing agent

¶ - Agent-executed installation of the Taller Agent System Kernel: interview the operator, render the kernel, place it in the harness, verify.

document:
  id: task.install@1
  version: 2.2.0
  status: active
  audience: the AI agent the operator pointed at this folder
  scope: preflight, interview, render, place, verify, report

You are installing a governance kernel into the harness you are running in. Read this file whole,
then follow the chapters in order. Talk to the operator in their language. Explain before you ask.

¶ 1 — Preflight

```text
package_root the folder containing this file
detect harness you are running in: claude_code | codex | antigravity | cline | other
detect os and home directory
require python >= 3.10 and git on PATH -> if missing, tell the operator how to install them and stop
python_cmd the exact command that runs Python 3 here (python | python3 | py -3)
kernel_home default ~/.task; operator may choose another path
read adapters/ADAPTERS.tdsl chapter for the detected harness
existing_install {{KERNEL_HOME}}/kernel.config.json present -> offer upgrade (keep answers) or reinstall
```

¶ 2 — Interview

Ask one topic at a time. For every option: say what it does, give pros and cons in one or two
lines each, state the default, accept "default". Use what you already know about the operator
(name, account, organisation, language) to suggest concrete values. Record answers for ¶3.

```text
signature:
  explain every source file the kernel indexes gets a header banner; the signature lines record
    who authored or indexed it, which helps provenance when code is shared or transplanted
  ask author line (e.g. "<Name> 2026", "<Org> Dev 2026") or none
  suggest options built from the operator's name, organisation and current year
  none -> accepted without pushback; the line is omitted
  tagline default "VAI CORINTHIANS!" # see README; mention it plainly, the operator may change or remove it

operator_profile:
  identity name and role, or "anonymous"
  domain field of work the agent should assume as context
  capability how technical the operator is (shapes explanation depth)
  shared_context topics the agent must not over-explain

chat_language:
  explain language the agent uses with the operator; code, identifiers and comments stay English
  default the language the operator is using now

agent_posture:
  options thought_partner (pushes back, flags risks unasked) | executor (does what is asked, minimal debate)
  default thought_partner

response_style:
  options:
    dense ban [cosmetic_preamble step_by_step_narration inter_call_recap end_of_response_summary list_bullets redundant_headers]
      pro fastest to read, lowest token cost; con fewer visual cues, harder to skim long answers
    balanced ban [cosmetic_preamble step_by_step_narration inter_call_recap]
      pro readable lists and headers; con longer answers
  default balanced

commit_attribution:
  options no_agent_trailer (commits carry only the operator as author) | allow_agent_trailer
  pro_no authorship stays with the human who reviewed it; con hides AI involvement from collaborators
  default no_agent_trailer

doc_edits:
  options require_explicit_request | allowed_when_relevant
  pro_require avoids unsolicited documentation churn; con docs may lag behind code
  default require_explicit_request

sdd_default_mode:
  explain spec-driven development records constitution, spec, plan, tasks and analysis before code
  options:
    gradual one feature goes from spec to execution before the next starts
      pro feedback from real code early; con architecture decided piecemeal
    integral every feature is specified, planned and tasked before any code
      pro whole architecture settled and reviewable up front; con more planning before first result
  default gradual; switchable per project with `sdd_gate.py mode <value>`

execution_authority:
  options interactive | autonomous
  default interactive
  independent_of planning_mode
  autonomous requires explicit constitution scope, stop conditions and closure authority
  project_config .task/execution.config.tdsl; autonomous_authorized remains false until explicit grant
  legacy_upgrade never enables autonomy implicitly

execution_topology:
  max_active_subagents positive integer, default 1
  separate_test_author boolean, default true
  parallel_requires independent units and exclusive source, journal, report and temporary destinations
  combined_test_authorship never weakens independent criteria or orchestrator-owned test gate


test_stance:
  options required (tests alongside code, never skipped) | operator_decides (agent proposes, operator chooses)
  default required
```

¶ 3 — Render

```text
1 create {{KERNEL_HOME}}; copy all children of kernel/ into it, preserving their relative paths
  include all nine departments plus scripts, docs, grammar, skills, templates and policy.tdsl.md
  scripts are compatibility entrypoints; departmental implementations are required dependencies
  copy LICENSE into {{KERNEL_HOME}}; preserve its notices and terms
  copy adapters/ into {{KERNEL_HOME}}/adapters for installed-layout validation; this does not activate hooks
2 copy the harness hook script (adapters/<harness>/*_hook.py) into {{KERNEL_HOME}}/scripts/ when the harness has hooks
3 write {{KERNEL_HOME}}/kernel.config.json from kernel.config.example.json with the interview answers
4 render kernel/policy.tdsl.md -> {{KERNEL_HOME}}/policy.tdsl.md, replacing every {{PLACEHOLDER}}:
    KERNEL_HOME absolute path with forward slashes
    OPERATOR_IDENTITY OPERATOR_DOMAIN OPERATOR_CAPABILITY SHARED_CONTEXT from operator_profile
    AGENT_POSTURE CHAT_LANGUAGE SDD_DEFAULT_MODE TEST_STANCE from their answers
    BANNED_OUTPUT and RESPONSE_BANS from response_style (TDSL collection form)
    COMMIT_ATTRIBUTION_RULE "ban Co-Authored-By trailer for AI agents" | "allow agent trailer when the harness adds one"
    DOC_EDIT_RULE "require_explicit_request" | "allowed_when_relevant"
5 render {{KERNEL_HOME}}/docs/engineering.tdsl placeholders (SIGNATURE_AUTHOR SIGNATURE_TAGLINE OPERATOR_ORG OPERATOR_MISSION)
6 replace {{KERNEL_HOME}} in every copied .md, .tdsl and .template file
  copy grammar/schema JSON bytes verbatim; do not render or normalize pinned schema files
7 verify no `{{` remains in {{KERNEL_HOME}} except inside kernel.config.example.json
```

¶ 4 — Place

```text
follow adapters/ADAPTERS.tdsl for the detected harness:
  back up every file you will touch into {{KERNEL_HOME}}/backups/<timestamp>/
  policy merge between `<!-- task:begin -->` and `<!-- task:end -->`; replace only that block on upgrade
  skills copy {{KERNEL_HOME}}/skills/* recursively into the harness skill directory, including agents/openai.yaml
  keep allow_implicit_invocation=false for execute; harnesses without this setting follow its explicit-command contract
  hooks merge the adapter hook config with {{PYTHON}} -> python_cmd and {{KERNEL_HOME}} resolved;
    keep the operator's existing hooks
operator_has_several_harnesses -> offer to place the same kernel into each; one kernel_home serves all
```

¶ 5 — Verify

```text
1 python {{KERNEL_HOME}}/scripts/selftest.py -> must print "selftest: OK"
  python -m unittest discover -s {{KERNEL_HOME}}/scripts -p "test_*.py" -> must pass
2 python {{KERNEL_HOME}}/scripts/diagram_check.py render header --file demo.py
    --project demo --version 0.1 --purpose "install check" -> shows the chosen signature lines
3 confirm the harness sees the skills (list them, or ask the operator to restart the harness)
fail -> report the exact output; do not mark the install done
```

¶ 6 — Report

```text
tell the operator, in their language:
  what was installed and where (kernel_home, policy file, skills directory, hooks)
  the choices recorded, and that they live in {{KERNEL_HOME}}/kernel.config.json and the policy file
  how to start: "start a governed project" -> skill(protocol); "index this code" -> skill(diagram) or skill(code-map)
  where backups are and how to uninstall (remove the task block, the copied skills, the hook entries, kernel_home)
```

¶ 7 — Upgrade Projects Explicitly

upgrade:
  kernel: back_up_installed_copy_and_operator_configuration
  project: inspect_existing_records_and_execution_authority_before_migration
  command: python {{KERNEL_HOME}}/scripts/execution_runtime.py --root <project> migrate
  legacy: preserve_planning_records_and_feature_execution_journals
  autonomy: explicit_opt_in_only_never_implied_by_integral
  identity: initialize_registry_without_mutating_original_source
  unresolved_move: reconcile_explicitly_without_identity_guess
  constitution: preserve_each_existing_published_version
  verify: query_registry_and_compare_runtime_projection_before_resume
rule: installation_upgrade_does_not_publish_merge_or_deploy_project_changes

¶ 8 — Departmental Upgrade and Loop Verification

upgrade_2_2:
  contract: {{KERNEL_HOME}}/integration/installation/layout.tdsl
  manifest: {{KERNEL_HOME}}/system/routing/departments.json
  backup: distribution_files_before_replacement_and_existing_operator_configuration
  preserve: kernel_configuration_personal_skills_existing_harness_hooks_and_consumer_project_records
  migrate: kernel_implementation_locations_only_not_project_schemas_or_journals
  compatibility: keep_public_script_and_skill_names_and_sibling_imports
  context: compact_session_snapshot_is_optional_observed_context_not_warm_cold_configuration
  validation: run_installed_tests_and_selftest_with_departmental_dependencies_present
rule: L02_L04_L08_are_instruction_contracts_and_do_not_require_complete_hook_interception
rule: never_commit_from_PostToolUse_or_decide_semantic_sufficiency_in_a_hook
rule: installing_the_distribution_does_not_authorize_project_execution_or_Git_effects
