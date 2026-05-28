# Raw Data Staging for Zenodo

This directory is intentionally excluded from Git history.

Place raw archives in `data/raw_archives/` before creating the Zenodo deposit. Existing archive candidates on `Z:/` include:

- `Z:/ned3-004_BoilingAcousticsHydrophone.zip`
- `Z:/ned3-005_Hit2Flux.zip`
- `Z:/ned3-006_BoilingImageSequence.zip`

For `ned3-007`, create an archive from `Z:/ned3_007_MultimodalBoilingData` or upload the folder structure directly if Zenodo upload tooling supports it.

After staging, run:

```powershell
python scripts/generate_manifest.py --root . --output MANIFEST.csv --checksums
python scripts/validate_splits.py
```
