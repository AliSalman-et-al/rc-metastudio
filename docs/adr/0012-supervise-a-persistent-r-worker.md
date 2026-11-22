# 0012. Supervise a persistent R worker

Status: Accepted. The embedded backend remains the default during migration.

The embedded R call stack prevents Qt from reliably handling input and repainting.
An R condition can return to that stack, but a hung native call cannot be interrupted
safely and a process fault takes down the desktop. Stage A reduced computation costs.
On Windows, the 400-study fixture still produced event-loop gaps of 0.47 seconds
for a cold fit and 5.63 seconds for trial sequential analysis.

Launch one private R child per desktop session and keep it warm across projects.
The startup handshake checks the protocol, RCMetaR version and source stamp, and
pinned R package versions. Load the workflow namespaces and initialize the
production graphics devices before marking the child ready. Repeat that warmup
on every respawn.

Use stdin and stdout for UTF-8 JSON frames with an eight-digit ASCII hex byte
length. R exposes binary stdin and byte-preserving text output on stdout.
R sends console output to stderr with `sink()`. Qt drains stderr separately.
Pipes avoid a listening port, authentication and firewall prompts. Consider
loopback TCP only if pipes fail platform qualification.

Each request has a version, ID and typed operation. A job returns one matching
terminal response with its operation's result or a cancellation or failure.
Reject malformed frames, unexpected IDs and oversized messages. Only one job
uses the child at a time. Keep the Qt event loop running while it is busy.
Cancel marks the current job for cooperative exit at a checkpoint. If the
child hangs or misses the cancellation deadline, terminate it and start a new
child. A crash also starts a fresh child. Surface the interrupted job to the
user and allow an explicit retry.

Qt owns project state, cached previews and the files it publishes. R owns
the interpreter, numerical objects and graphics devices. Bind each job to
its input snapshot and discard cancelled or stale work. Give work that produces
files a job-owned staging directory. Qt validates and publishes those files
only after success, so an interrupted job leaves committed results usable.

Enable the worker with `RCMS_R_BACKEND=worker`. Migrate calculators and study
previews first, then fitting and trial sequential analysis, then plots and
exports. Qualify packaged Windows, macOS and Linux before changing the default
and removing the embedded integration.
