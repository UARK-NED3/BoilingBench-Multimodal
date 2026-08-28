# Baselines

The v0.1 benchmark should include simple baselines before advanced deep-learning models:

1. Constant and moving-average predictors for heat flux.
2. Linear regression or ridge regression on summary acoustic/image features.
3. Random forest or gradient boosting on engineered features.
4. Sequence-regression baselines using SeqReg-compatible windows.
5. Modality-ablation baselines for multimodal fusion.

Baseline notebooks should record preprocessing, split file, random seed, package versions, and metric output.

**Reference baseline contributions:** [`baselines/chfwatch/`](chfwatch/) adds
a public processed-data exploratory baseline for BoilingBench-3/4. It uses
leave-one-dataset-out evaluation, records train-only preprocessing, and keeps
unconfirmed CHF proxy events out of the target and safety metrics.
