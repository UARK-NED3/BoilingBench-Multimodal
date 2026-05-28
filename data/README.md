# Raw Data Staging for Zenodo

This directory is intentionally excluded from Git history.

Place raw archives in `data/raw_archives/` before creating the Zenodo deposit. Existing archive candidates on `Z:/` include:

- `Z:/ned3-004_BoilingAcousticsHydrophone.zip`
- `Z:/ned3-005_Hit2Flux.zip`
- `Z:/ned3-006_BoilingImageSequence.zip`

For `ned3-007`, the folder structure is staged directly at `data/raw_archives/ned3-007_MultimodalBoilingData`. Upload the folder contents directly if your Zenodo workflow supports bulk upload, or create and verify a separate archive before upload.

After staging, run:

```powershell
python scripts/generate_manifest.py --root . --output MANIFEST.csv --checksums
python scripts/validate_splits.py
```
