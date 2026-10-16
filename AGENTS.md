# Working on 9b7 Linux

Read `docs/HANDOFF.md` and `README.md` first. Update the handoff after each meaningful milestone with exact test results, unresolved issues, and the next command. The user explicitly requests incremental commits and pushes.

Use the existing checkout. Do not create Git worktrees unless requested. Keep build outputs, runtime data, credentials, and ISO files out of Git. Never mark an unbooted image as release-ready. Preserve TLS, package signatures, and artifact checksums. Record upstream licenses and provenance.

Run `python3 -m unittest discover -s tests -v` and `bash scripts/check.sh` before committing code changes. Build the ISO in a dedicated privileged builder; never install the live image onto a development host disk. Do not run disk-erasing commands without an explicit target and confirmation from the person installing.
