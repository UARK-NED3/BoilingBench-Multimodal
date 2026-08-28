# GPU and full-archive run summary

## Release and archive

- Source: `hanhuark/BoilingBench-Multimodal`
- Revision: `e4d977db425e5a283c5f26b13b452a84868a5c5a`
- Archive verification: `pass`
- Expected and observed files: `6,915`
- Expected and observed bytes: `33,193,155,778`
- Missing, size-mismatched, or extra files: `0 / 0 / 0`
- Storage location: external data directory on the GPU host; raw archive data is not tracked in Git.

## Compute

Both experiments ran with `device=cuda` on `NVIDIA RTX PRO 5000 Blackwell Generation Laptop GPU`. The exact command-line settings and PyTorch metadata are stored in the two JSON result files.

## Visual bubble-area regression

The model was fit only on the public BubbleID base `Classes-1/Train` split and evaluated on the explicit base `Test` split. Flow-boiling and new-facility data were evaluation-only.

| Evaluation set | n | Mean baseline MAE | Mean model MAE | Mean R2 |
| --- | ---: | ---: | ---: | ---: |
| Base test | 125 | 0.0788 | 0.0187 | 0.914 |
| Flow external | 130 | 0.1754 | 0.5571 | -12,214 |
| New-facility external | 24 | 0.2383 | 0.1165 | 0.478 |

These results support a useful in-domain visual diagnostic and show partial new-facility transfer. Flow transfer is a clear failure: its annotation/image distribution differs sharply from the base training data, so the constant baseline is safer than this model there. The target is polygon area fraction derived from human annotations, not a CHF label.

## Temporal heat-flux regression

The temporal model uses thermocouple and pressure sequences, resampled to 10 Hz, with leave-one-dataset-out evaluation across BB-1 through BB-4. Window counts are `BB-1=610`, `BB-2=966`, `BB-3=340`, and `BB-4=234`; windows are not independent physical runs.

| Held-out dataset | n | Baseline MAE (W/cm2) | Mean model MAE (W/cm2) | Mean R2 |
| --- | ---: | ---: | ---: | ---: |
| BB-1 | 610 | 144.8 | 144.9 | -2.176 |
| BB-2 | 966 | 80.3 | 994.0 | -15,324 |
| BB-3 | 340 | 50.2 | 14.7 | 0.577 |
| BB-4 | 234 | 43.3 | 6.3 | 0.864 |

The held-out results are dominated by dataset shift in absolute heat-flux scale and operating conditions. BB-3 and BB-4 transfer is promising as a diagnostic, while BB-1 is baseline-level and BB-2 is unstable. No pooled score should be used to claim general CHF detection.

## Validation assessment and next step

This is **share with caveats** evidence for reproducibility and failure analysis, not a validated CHF benchmark. The release currently provides one processed run per BB-1 through BB-4, and the heat-flux target is a derived product rather than an independent physical CHF measurement. The next high-value experiment is to add multiple independently labeled run-level cases with confirmed event provenance, then repeat grouped evaluation without allowing adjacent windows from one run to stand in for independent samples.

Reproduce the archive check with `scripts/verify_public_archive.py`, the visual run with `scripts/train_gpu_bubble_area.py`, and the temporal run with `scripts/train_gpu_temporal_heat_flux.py`.
