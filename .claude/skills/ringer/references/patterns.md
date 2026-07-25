## Pattern playbook

Reach for a named pattern before inventing one. Skeletons in `templates/`:

| Kit | Use when |
|---|---|
| [review-swarm](../../../../templates/review-swarm/) | You need broad read-only review coverage before deciding what to fix. |
| [fix-swarm](../../../../templates/fix-swarm/) | You have confirmed independent fixes that can be split across isolated worktrees. |
| [focus-group](../../../../templates/focus-group/) | You need isolated persona feedback on a product, pitch, prompt, or workflow. |
| [bakeoff](../../../../templates/bakeoff/) | You need evidence for choosing a model, prompt, or configuration across shared scenarios. |
| [research-with-proof](../../../../templates/research-with-proof/) | You need research backed by a proof task whose check executes the claim. |
| [launch-kit](../../../../templates/launch-kit/) | You need a go-to-market package built across research, persona review, and final assembly rounds. |
| [asset-swarm](../../../../templates/asset-swarm/) | You need media assets produced in parallel with executable checks for renders, batches, diagrams, or captures. |
| [adversarial-review](../../../../templates/adversarial-review/) | You want several models to review the same artifact before the orchestrator synthesizes findings. |
| [repo-feature](../../../../templates/repo-feature/) | You know what to build and need sandboxed workers to edit a real repo with build and git checks. |
| [migration-swarm](../../../../templates/migration-swarm/) | You have mechanical codebase transforms that can be partitioned across worktrees. |
| [doc-swarm](../../../../templates/doc-swarm/) | You need module docs with executed examples and checks against invented APIs. |
| [test-hardening](../../../../templates/test-hardening/) | You need stronger tests by module while keeping production source edits off-limits. |
| [competitive-teardown](../../../../templates/competitive-teardown/) | You need competitor research with citation allowlists and a synthesis phase. |
| [data-pipeline](../../../../templates/data-pipeline/) | You need fetch, transform, and validate stages with executed validators and honesty rules. |
| [probe](../../../../templates/probe/) | You need a one-task manifest for a smoke, probe, or post-mortem. |

Pattern-selection judgment:

- **Browse the catalog first.** Before writing any manifest, browse
  `templates/README.md`: choose a kit, mix pieces from several, or write
  your own having seen the prior art.
- **Review before fix.** Run a read-only review swarm, read the reports
  yourself, then compile the confirmed findings into a fix-swarm manifest.
  Don't let the same worker find and fix.
- **Personas must be separate workers.** Parallel personas in one context
  bleed into each other. One persona per task, one session dir per task.
- **Iterating on a prompt/product? Re-run the same panel.** A fixed persona
  panel across rounds tells you whether a change fixed what the panel
  actually complained about.
- **Probes, smokes, and diagnosis loops are manifests too.** A model-calling
  smoke test is a one-task manifest with the transcript as `expect_files`
  and a validator as the check. Diagnosing a failed worker's output is a
  read-only scout task. If it calls a model, it runs under Ringer — that is
  what makes it visible, verified, and logged.
