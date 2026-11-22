# 0012. Supervise a persistent R worker

Status: Accepted. The worker is the only R backend.

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

Use stdin and stdout for UTF-8 JSON frames. A fixed marker precedes an
eight-digit ASCII hex byte length. Qt drains every complete frame and logs
bytes emitted outside frames. R sends console output to stderr with
`sink()` and clears the output sink stack before writing each reply.
Pipes avoid a listening port, authentication and firewall prompts. Consider
loopback TCP only if pipes fail platform qualification.

Each request has a version, ID and typed operation. A job can send progress
frames and returns one matching terminal response with its result,
cancellation or failure.
Reject malformed frames, unexpected IDs and oversized messages. Only one job
uses the child at a time. Keep the Qt event loop running while it is busy.
Calculator and preview jobs declare short deadlines. Fits, trial sequential
analysis, plots and exports have no wall-clock deadline. Progress frames
serve as heartbeats. A missing heartbeat reports a stall while leaving
Cancel available, since long native calls can finish without a checkpoint.
Cancel marks the current job for cooperative exit. If the child misses the
cancellation grace period, terminate it and start a new child. A crash also
starts a fresh child. Surface the interrupted job and allow an explicit retry.

Bind the worker to the desktop lifetime. Windows uses a kill-on-close Job
Object. Linux uses a separate process group and a parent watcher. macOS
combines stdin EOF with a parent watcher that can stop a busy child.

Qt owns project state, cached previews and the files it publishes. R owns
the interpreter, numerical objects and graphics devices. Bind each job to
its input snapshot and discard cancelled or stale work. Give work that produces
files a job-owned staging directory. Qt validates and publishes those files
only after success, so an interrupted job leaves committed results usable.
