# BoilingBench-Multimodal v0.1

BoilingBench-Multimodal v0.1 is a seed benchmark initiative for machine learning with two-phase boiling data. It is designed as a community starting point rather than a final field standard. The benchmark defines initial tasks, metadata, split logic, baseline expectations, and contribution mechanisms for acoustic, image, and multimodal boiling datasets.

## Scope

The v0.1 release is seeded from NED3 open datasets and local archives:

| Dataset ID | Local source | Benchmark role | Modalities |
|---|---|---|---|
| `ned3-004` | `Z:/ned3-004_BoilingAcousticsHydrophone` | hydrophone-to-heat-flux starter task | hydrophone, temperature, heat flux, images |
| `ned3-005` | `Z:/ned3-005_Hit2Flux` | acoustic-emission heat-flux task | AE hits, AE waveforms, hydrophone, pressure, temperature |
| `ned3-006` | `Z:/ned3-006_BoilingImageSequence` | image/video and hydrophone sequence task | high-speed video, hydrophone, temperature |
| `ned3-007` | `Z:/ned3_007_MultimodalBoilingData` | multimodal steady/transient boiling task | acoustic, optical, thermal, operating data |

Raw data are not stored in Git. GitHub hosts the benchmark control plane: documentation, metadata, task definitions, split files, manifests, and scripts. Raw archives should be deposited on Zenodo, Dataverse, Dryad, or another data repository and cited by DOI.

## Benchmark Tracks

1. **Acoustic heat-flux regression**: predict heat flux from hydrophone or AE time histories.
2. **AE hit heat-flux regression**: predict heat flux from hit-level AE features and waveform-derived features.
3. **Image/video heat-flux regression**: predict heat flux from high-speed images, video windows, or image-derived features.
4. **Multimodal fusion**: combine acoustic, optical, thermal, and operating-condition signals.
5. **Transition/regime analysis**: classify boiling state, hysteresis branch, or transition indicators where labels are available.

## What Makes This a Benchmark

Each track should provide raw data, processed data or processing scripts, task definitions, fixed train/validation/test splits, leakage rules, baseline models, evaluation metrics, and physical metadata. Splits should be by run, surface, heat-load path, or dataset source, not by randomly mixed adjacent frames or windows.

## Repository Layout

```text
baselines/          Baseline model notes and future notebooks
metadata/           Dataset card, machine-readable metadata, schema
scripts/            Manifest, split validation, and checksum utilities
splits/             Fixed benchmark split files
tasks/              Task definitions and metrics
MANIFEST.csv        Source/raw archive inventory
README.md           Benchmark overview
```

## Zenodo Upload

For Zenodo, upload the contents of this folder plus `data/raw_archives/` after staging raw archives. The GitHub repository should exclude `data/raw_archives/` via `.gitignore`.

## Citation

If using this benchmark before a DOI is assigned, cite the GitHub repository and the underlying NED3 datasets. After Zenodo upload, cite the versioned Zenodo DOI for the benchmark archive.
