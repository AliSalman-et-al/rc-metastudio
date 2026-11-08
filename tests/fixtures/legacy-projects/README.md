# Frozen legacy project inputs

These seven sample archives are copied byte for byte from `sample_projects/` at historical source commit `322ede26d11d1a2564b87d266d16d416dde26b40`. They are test inputs for project migration, arm-name preservation and manuscript retention. They remain separate from current bundled examples and the frozen numerical expectations.

The source commit was available in the development repository but is not reachable from the published branch history. Tests read these tracked files directly so full clones, shallow clones and source archives use the same inputs without fetching historical Git objects.

Do not regenerate them from the current project writer to make migration tests pass. Their original Git blob IDs and SHA-256 digests are:

| File | Bytes | Original Git blob | SHA-256 |
| --- | ---: | --- | --- |
| BCG.rcms | 4235 | `8d0ed88992e4af44710c96e44ba5d5700490f474` | `ee66fecdcf79a36f665a27b8b02509a4e3478cb6a00362fe4d6e9c7e63f0f839` |
| NielWeise2008-IRR.rcms | 1691 | `230f24bee6b159ba67bd915afd7019abe75e64ed` | `4b0ba4c9c515da90a5768b4729886ccfb73a5ef4f239321ff1daca01b13ebb12` |
| Pignon2000-HR.rcms | 5000 | `9f10c958242de65e73057a9b0c63ad8c6ff4328a` | `17e94f1436a1be97a5e14f3cf3ff8db3818198f4a1132ba0b32fb0976ade86f9` |
| amino.rcms | 9501 | `8a270bb6a8fd780de1a7b85f0956c863af8f756b` | `374681cc5f740f06d39a117047e4133b745dd8ae30c4974f5ab7c9f94d90b763` |
| continuous.rcms | 1802 | `456a5443d377e6f4297043f0247421627b3d3cac` | `025ae202f23eed7da8d5bc02aa0fa6d6e4d89b4f78179a5d1a3831c0a6d59093` |
| lymph.rcms | 8180 | `3a8355dfba55125f538e87b405abbbcfb771f3cd` | `2af63bc180d118a1729b79327563bfbdc67de909296c5f8d07dda14cd84d4fcb` |
| meantime.rcms | 8650 | `ab3a7d84edac1e2c8d5ca1582c40897d4f7bcd0a` | `0d173e541e34ab6b4e7c40ed6d2e81e38e6f1f4e5a79a41367914f4b568db88c` |
