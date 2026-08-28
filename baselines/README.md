# Baselines

The v0.1 benchmark should include simple baselines before advanced deep-learning models:

1. Constant and moving-average predictors for heat flux.
2. Linear regression or ridge regression on summary acoustic/image features.
3. Random forest or gradient boosting on engineered features.
4. Sequence-regression baselines using SeqReg-compatible windows.
5. Modality-ablation baselines for multimodal fusion.

Baseline notebooks should record preprocessing, split file, random seed, package versions, and metric output.

**Reference baseline contributions:** [`baselines/chfwatch/`](chfwatch/) adds a
transition-warning reference baseline for the `multimodal_fusion` task on
NED3-007 (pinned standalone repo, LSO splits, conformal calibration, OOD
flag, quantile-directional bands). Provisional numbers and reproduction
instructions live in its README.
