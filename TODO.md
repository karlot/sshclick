# SSHClick TODO

## Near Term

- TUI workflow polish
  - Refine the new host/group/config drawers and action flows in `ssht`
  - Keep action selection in centered modals, and use drawers for larger forms
  - Review validation, defaults, and field grouping after more manual usage

- Broader command coverage
  - Add more higher-level tests for modifying CLI commands and write flows
  - Add more app-level Textual tests for interactive TUI flows beyond browsing and reload
  - Cover create/edit/delete behavior now that the shared mutation layer is in place

- CLI/TUI workflow cleanup
  - Keep migrating remaining write flows to the shared `ops` layer where it improves consistency
  - Use the shared operations as the only mutation path for upcoming TUI forms
  - Review CLI output/reporting so success and error handling stay consistent across commands

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
