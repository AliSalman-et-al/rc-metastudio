# Installed-package CI integration proof

The Full R Stack verify() calls verify_analysis_authorities after installation,
before bridge/desktop checks. The helper always uses --installed, removes stale
JSON, rejects a nonzero R exit, an empty/inconsistent inventory, a false overall
status or any case without passed=true. Success prints count and elapsed seconds.
The uploaded report is artifacts/verification/rcms/authorities.json.

Local commands source ../env.sh. Base RCMetaR was installed with:
R CMD INSTALL -l "$PWD/artifacts/statistical-mutants/ci-integration/base-library" r/RCMetaR
Then R_LIBS was prepended with that private library and prove.py called the
same production helper used by verify(). base-install.log records installation.
The initial base run passed all 103 numerical cases but rejected four existing
subgroup rows lacking status metadata. Their records now emit passed=true only
after the unchanged assertions. restored.sh reruns against the clean installation.
mutant.sh records git apply, private installation and the exact helper invocation;
its EXIT trap reverses only that patch. mutant.log must fail at the t p-value.
No package was installed into the shared warm library. Libraries are not committed.

Linux/macOS: fast-verification.yml invokes Linux native/Python checks and macOS
verify.py smoke --require-r-evidence (verify_rcmetar_r_default.py). Neither calls
verify_rcmetar_r_stack.py. Workflow selection and those commands are unchanged.
The sharding branch's desktop_shard selector is checked using getattr so this
step runs for --skip-desktop and ordinary full verification, never desktop shards.
