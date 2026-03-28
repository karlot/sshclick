# SSHClick TODO

## Deferred Features

- Include-aware editing and write-back
  - Current support is intentionally limited to top-level `Include` parsing in read-only mode
  - Future work should decide how host/group edits map back to source files safely
  - Group-level edits across multiple included files need explicit rules before implementation

- Include-aware UI/CLI polish
  - Show clearer read-only warnings when configuration is locked because of `Include`
  - Expand source/location visibility where it improves browsing and debugging

- Broader command coverage
  - Add more higher-level tests for modifying CLI commands and write flows

- TUI editing roadmap
  - Re-enable edit/create/delete features only after file write safety rules are stronger

- Parser and config edge cases
  - Review additional OpenSSH config constructs and unsupported keywords incrementally
