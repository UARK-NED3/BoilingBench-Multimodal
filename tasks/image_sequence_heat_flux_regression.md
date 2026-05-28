# Task: Image/Video Heat-Flux Regression

## Input

High-speed boiling image frames, image windows, video clips, or image-derived features such as bubble count, bubble area fraction, nucleation-site density, interface masks, optical flow, or learned visual embeddings.

## Target

Heat flux, boiling state, transition indicator, or derived physical quantity depending on the split file and dataset.

## Metrics

- Regression error for heat flux
- Classification metrics for regime or transition labels
- Segmentation metrics when mask labels are used
- Physical-feature error for bubble count, area fraction, departure frequency, or nucleation-site statistics

## Leakage Rules

Do not mix frames from the same video across train, validation, and test unless the task is explicitly a within-video interpolation benchmark.
