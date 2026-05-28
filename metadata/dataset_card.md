# Dataset Card: BoilingBench-Multimodal v0.1

## Intended Use

This seed benchmark supports reproducible development of machine-learning models for two-phase boiling heat transfer. It is intended for acoustic heat-flux regression, acoustic-emission learning, image/video heat-transfer inference, multimodal fusion, and transition/regime analysis.

## Motivation

Two-phase heat-transfer ML studies are difficult to compare because datasets differ in sensors, surfaces, operating conditions, labels, preprocessing, and split protocols. BoilingBench-Multimodal v0.1 starts from NED3 public datasets to define a reusable benchmark structure that the community can extend.

## Data Modalities

- Hydrophone and acoustic-emission time histories (`0+1D`)
- Temperature, pressure, and operating-condition time series (`0+1D`)
- High-speed boiling images and videos (`2+0D`, `2+1D`)
- Derived heat-flux labels and transition indicators where available
- Multimodal synchronized records for steady and transient boiling

## Known Limitations

The v0.1 seed benchmark is primarily based on one laboratory ecosystem. It is useful for establishing benchmark mechanics, but field-level generalization will require contributions from additional laboratories, fluids, geometries, pressures, surfaces, and diagnostics.

## Recommended Reporting

Papers using this benchmark should report the benchmark version, task name, split file, raw dataset DOI, preprocessing script, model inputs, target labels, metrics, uncertainty treatment, and failure cases.
