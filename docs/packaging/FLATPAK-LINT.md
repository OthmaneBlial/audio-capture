# Retired sandbox-lint note

The previous sandbox package had a local metadata exception for its application
identifier. That exception is inactive: the current release workflow builds
native Rust archives and does not run a sandbox linter. It must not be cited as
distribution approval or as evidence for the current application.

If a future sandbox package is proposed, create a new manifest, permission
review, offline build, install/removal test, and distribution review from the
current Rust source. Do not revive the old workflow or its permissions by
copying this note.
