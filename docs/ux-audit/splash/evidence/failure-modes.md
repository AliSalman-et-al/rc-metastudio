# Startup proof obligations (written before implementation/tests)

- R imports or a main window appears before the splash is painted.
- Package steps fail to repaint the live status, or text/artwork lose DPI precision.
- Rounded corners become opaque; splash lacks taskbar identity or is off-screen.
- Successful startup leaves disabled controls, a wait cursor, stale status or a splash.
- R or a late package fails: splash leaks, shell never opens, editing is disabled, analysis is enabled, or the existing error dialog is absent.
- Positional startup/project smoke bypasses the splash or fails to open its input.
- Noninteractive composition, required in-process R, callbacks or teardown regress.

Proof: real Qt/R desktop driver observes each load boundary and ready shell; native startup probe at scale 1/2 captures the live splash and shell, then injects a grid-load error after actual R/metafor/RCMetaR loading and observes the real modal error and editable project. Existing positional smoke and GUI teardown/geometry lanes cover their entry points.

Review follow-up obligations, recorded before the follow-up implementation:
- The shell is visible but unpainted behind the startup modal error.
- The error describes Method & Parameters instead of failed R startup, or omits
  the pinned-runtime install/repair and restart instructions.
Proof: observe a real main-window Paint event before the existing modal dialog,
assert its complete startup message, and capture the desktop while it is open.
