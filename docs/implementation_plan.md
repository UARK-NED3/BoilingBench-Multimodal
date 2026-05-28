# BoilingBench-Multimodal v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a seed benchmark package for multimodal two-phase boiling datasets, with GitHub-ready control files and a Zenodo-ready data archive folder.

**Architecture:** Keep GitHub lightweight by storing benchmark docs, task definitions, metadata schemas, split files, manifests, and scripts. Store raw large dataset archives in a separate local `data/raw_archives/` folder for Zenodo upload.

**Tech Stack:** Markdown, YAML, CSV, Python standard library, GitHub CLI, Zenodo upload by user.

---

### Task 1: Package Scaffold

**Files:** create benchmark root directories and core docs.

- [x] Create root directory at `C:\Users\hanhu\Documents\Manuscripts\benchmarks\BoilingBench-Multimodal-v0.1`.
- [x] Create `docs`, `metadata`, `splits`, `tasks`, `scripts`, `baselines`, `data/raw_archives`, and `data/samples`.

### Task 2: Benchmark Definition

**Files:** `README.md`, `metadata/dataset_card.md`, `metadata/metadata.yaml`, `tasks/*.md`.

- [x] Define seed benchmark scope using NED3 datasets `ned3-004`, `ned3-005`, `ned3-006`, and `ned3-007`.
- [x] Define benchmark tracks for acoustic heat-flux regression, AE heat-flux regression, image-sequence heat-flux regression, multimodal fusion, and transition/regime analysis.
- [x] Define leakage rules, intended splits, and evaluation metrics.

### Task 3: Manifests and Splits

**Files:** `MANIFEST.csv`, `splits/*.csv`, `scripts/*.py`.

- [x] Generate a source manifest from local `Z:\` dataset folders.
- [x] Generate fixed v0.1 split files by run/dataset unit rather than random frame/window splits.
- [x] Add scripts for manifest generation and split validation.

### Task 4: Zenodo Raw Data Package

**Files:** `data/raw_archives/*.zip`, `data/README.md`.

- [x] Include instructions for placing or copying raw archives from `Z:\`.
- [ ] Copy large raw archives after docs and GitHub repo are validated.

### Task 5: GitHub Repository

**Files:** Git repo excluding `data/raw_archives/`.

- [ ] Create `UARK-NED3/BoilingBench-Multimodal`.
- [ ] Push docs, scripts, manifests, splits, and metadata.
- [ ] Keep raw data out of Git history.
