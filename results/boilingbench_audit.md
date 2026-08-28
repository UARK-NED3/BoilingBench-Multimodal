# BoilingBench current-release audit

- Hugging Face revision: `e4d977db425e5a283c5f26b13b452a84868a5c5a`
- Generated: `2026-08-28T16:07:08.027739+00:00`
- Scope: public processed exports; no raw files copied into this repository

| Dataset | Status | Duration (s) | Samples | Hydrophone | Microphone | AE hits | Continuous AE | CHF status |
|---|---|---:|---:|---|---|---|---|---|
| BB-1 | pass | 988.9 | 9890 | True | False | True | True | not_confirmed |
| BB-2 | pass | 1556.9 | 15570 | True | False | True | True | not_confirmed |
| BB-3 | pass | 555.990772 | 1674672 | True | True | True | False | not_confirmed |
| BB-4 | pass | 385.993492 | 1162632 | True | True | True | False | not_confirmed |

## Interpretation

The current package supports cross-dataset heat-flux regression and modality-availability audits. It does not support a confirmed-CHF alarm benchmark: `chf_proxy` is marked `not_confirmed`. The processed target is an analysis product derived from the thermal data, so thermal-regression metrics are not independent physical validation.

## Warnings

- BB-1: microphone band-power export is absent
- BB-1: continuous AE is represented by processed band-power; raw waveform arrays are not audited
- BB-1: processed heat flux and chf_proxy are not confirmed CHF labels
- BB-2: microphone band-power export is absent
- BB-2: continuous AE is represented by processed band-power; raw waveform arrays are not audited
- BB-2: processed heat flux and chf_proxy are not confirmed CHF labels
- BB-3: continuous AE waveform feature export is absent from this case
- BB-3: processed heat flux and chf_proxy are not confirmed CHF labels
- BB-4: continuous AE waveform feature export is absent from this case
- BB-4: processed heat flux and chf_proxy are not confirmed CHF labels
