# Task: Acoustic Heat-Flux Regression

## Input

Hydrophone or acoustic-emission time windows from boiling experiments. Inputs may be raw waveforms, spectrograms, event features, or learned sequence embeddings.

## Target

Heat flux at the corresponding time window. If labels are derived from temperature histories or heater power, the data-reduction method must be reported.

## Metrics

- Mean absolute error
- Root mean squared error
- Mean absolute percentage error where heat flux is positive and sufficiently above noise
- Error near transient regions or transition events
- Calibration or uncertainty metrics if probabilistic predictions are used

## Leakage Rules

Do not split overlapping or adjacent windows from the same experimental run across train, validation, and test. Prefer run-held-out, heat-path-held-out, surface-held-out, or dataset-held-out splits.
