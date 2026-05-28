# Zenodo Upload Checklist

Use this folder as the local Zenodo staging package:

`C:\Users\hanhu\Documents\Manuscripts\benchmarks\BoilingBench-Multimodal-v0.1`

## Files Already Staged

The following raw archives are present in `data/raw_archives/` and recorded in `MANIFEST.csv` with SHA256 checksums:

- `ned3-004_BoilingAcousticsHydrophone.zip`
- `ned3-005_Hit2Flux.zip`
- `ned3-006_BoilingImageSequence.zip`

## Large Folder Still To Archive

The `ned3-007` source folder is approximately 66.8 GB:

`Z:\ned3_007_MultimodalBoilingData`

Before final Zenodo upload, either:

1. Create a compressed archive of this folder and place it in `data/raw_archives/`, or
2. Upload the folder contents separately if using a Zenodo-compatible bulk upload workflow.

After staging `ned3-007`, refresh `MANIFEST.csv` with the file size and SHA256 checksum.

## Suggested Zenodo Metadata

- Title: `BoilingBench-Multimodal v0.1: A Seed Benchmark for Multimodal Machine Learning in Two-Phase Boiling Heat Transfer`
- Resource type: Dataset
- Version: `0.1`
- Related identifier: `https://github.com/UARK-NED3/BoilingBench-Multimodal`
- Keywords: boiling, two-phase heat transfer, machine learning, benchmark dataset, acoustic emission, hydrophone, infrared thermography, high-speed imaging, multimodal data
- Description: Use the top-level `README.md` and `metadata/dataset_card.md` as the starting point.

## Post-Upload Steps

1. Add the Zenodo DOI to `metadata/metadata.yaml`.
2. Add the Zenodo DOI to `CITATION.cff`.
3. Update the GitHub repository README with the DOI badge or DOI link.
4. Create a GitHub release matching the Zenodo version.
