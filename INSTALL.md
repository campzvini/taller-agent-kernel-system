# Install — instructions for the installing agent

¶ - Agent-executed installation of the Taller Agent System Kernel: interview the operator, render the kernel, place it in the harness, verify.

document:
  id: task.install@1
  version: 1.1.0
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

test_stance:
  options required (tests alongside code, never skipped) | operator_decides (agent proposes, operator chooses)
  default required
```

¶ 3 — Render

```text
1 create {{KERNEL_HOME}}; copy kernel/scripts, kernel/docs, kernel/grammar, kernel/skills, kernel/templates into it
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
7 verify no `{{` remains in {{KERNEL_HOME}} except inside kernel.config.example.json
```

¶ 4 — Place

```text
follow adapters/ADAPTERS.tdsl for the detected harness:
  back up every file you will touch into {{KERNEL_HOME}}/backups/<timestamp>/
  policy merge between `<!-- task:begin -->` and `<!-- task:end -->`; replace only that block on upgrade
  skills copy {{KERNEL_HOME}}/skills/* into the harness skill directory
  hooks merge the adapter hook config with {{PYTHON}} -> python_cmd and {{KERNEL_HOME}} resolved;
    keep the operator's existing hooks
operator_has_several_harnesses -> offer to place the same kernel into each; one kernel_home serves all
```

¶ 5 — Verify

```text
1 python {{KERNEL_HOME}}/scripts/selftest.py -> must print "selftest: OK"
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
