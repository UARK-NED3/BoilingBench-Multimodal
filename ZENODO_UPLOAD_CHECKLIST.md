# Zenodo Upload Checklist

Use this folder as the local Zenodo staging package:

`C:\Users\hanhu\Documents\Manuscripts\benchmarks\BoilingBench-Multimodal-v0.1`

## Files Already Staged

The following raw archives are present in `data/raw_archives/` and recorded in `MANIFEST.csv` with SHA256 checksums:

- `ned3-004_BoilingAcousticsHydrophone.zip`
- `ned3-005_Hit2Flux.zip`
- `ned3-006_BoilingImageSequence.zip`

The `ned3-007` source folder is also staged locally as a raw folder copy:

- `data/raw_archives/ned3-007_MultimodalBoilingData`

This folder contains 322 files and is inventoried in `MANIFEST_NED3_007_FILES.csv`.

## Optional Archive Step

If uploading many individual files to Zenodo is inconvenient, create a compressed or uncompressed archive of:

`data/raw_archives/ned3-007_MultimodalBoilingData`

The first attempt with Windows `tar` produced a truncated archive, so verify any large single-file archive before upload by listing its contents and checking its size.

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
