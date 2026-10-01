# Qualify Windows, macOS, and Ubuntu

The UI/UX rewrite must support and qualify Windows x64 (minimum Windows 10 version 1809), Apple silicon macOS (minimum macOS 14), and Ubuntu x64 (24.04 and 26.04 LTS), expanding the Ubuntu 24.04 scope in ADR 0013 to include Ubuntu 26.04. This accepts additional packaging and native verification work so Ubuntu is a supported release target. Intel macOS and ARM Ubuntu are outside this release scope; actual packaged applications must be qualified, because CI runner selection alone does not establish support.
