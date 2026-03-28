# SSHClick TODO

## Near Term

- Shared mutation layer for CLI and TUI
  - Extract create/edit/delete logic for hosts, groups, and config options out of Click commands
  - Reuse the same operation layer from both `sshc` and `ssht`
  - Return structured results so the TUI does not need to depend on CLI-shaped flows

- TUI edit/create flows
  - Add proper form-based create and edit flows in `ssht`
  - Keep action selection in centered modals, and use drawers for larger forms
  - Start with host create/edit before group editing flows

- Broader command coverage
  - Add more higher-level tests for modifying CLI commands and write flows
  - Add more app-level Textual tests for interactive TUI flows beyond browsing and reload
  - Cover create/edit/delete behavior once the shared mutation layer exists

- Include/read-only polish
  - Keep improving read-only signaling when config is locked because of `Include`
  - Expand source/location visibility where it improves browsing and debugging
  - Consider clearer UI labels for what actions are disabled and why

- TUI network view expansion
  - Extend the host `Network` tab with more diagnostics where it makes sense
  - Possible future additions: reachability, ping, traceroute, richer tunnel summary
  - Reuse existing core graph output wherever possible

## Future Design

- Parser and config edge cases
  - Review additional OpenSSH config constructs and unsupported keywords incrementally
  - Continue validating first-match/inheritance behavior against OpenSSH semantics

- Include-aware editing and write-back
  - Current support is intentionally limited to top-level `Include` parsing in read-only mode
  - Decide how host/group edits map back to source files safely
  - Group-level edits across multiple included files need explicit rules before implementation
  - Defer nested includes and in-block includes until the source/write model is clearer

- Release and demo polish
  - Refresh release/demo assets after the TUI settles more
  - Use VHS-generated demos for future visual examples instead of older recordings
