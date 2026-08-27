# Dataset cards

These cards are the canonical descriptions for the seven BoilingBench datasets. They are intentionally conservative about what is measured, what is derived by BoilingLab, and what is suitable as a machine-learning target.

## BoilingBench-1 — Ambient subcooled flat-Cu pool boiling

**Data type.** Multimodal transient pool-boiling experiment under ambient, subcooled conditions with a flat copper surface. The local package contains raw high-speed video, temperature, pressure, DC-power, hydrophone, acoustic-emission hit/time/source files, and continuous AE waveform data where the WFS file is present. The processed package contains synchronized thermal/acoustic tables, heat-flux and surface-temperature reconstructions, acoustic spectra, AE waveform features, critical-event markers, hysteresis products, and MEB analysis.

**Annotations.** Derived by BoilingLab post-processing. MEB is retained for this subcooled case; hysteresis outputs require a valid heat-load path and shutoff/DC-power trace. These are derived labels, not manual frame annotations.

**Primary tasks.** Multimodal heat-flux regression; acoustic and AE waveform representation learning; MEB/transition detection; leakage-safe temporal forecasting; uncertainty-aware sensor fusion.

**Citation.** Z. N. Prince, M. I. Hossain, S. Pierson, and H. Hu, “Coupled Thermal and Acoustic Signatures of Slow Modulation in Microbubble Emission Boiling,” manuscript in preparation. Cite the benchmark release as well.

## BoilingBench-2 — Subatmospheric saturated flat-Cu pool boiling

**Data type.** Multimodal transient pool boiling at subatmospheric pressure with a flat copper surface. Raw modalities include high-speed video, temperature, pressure, DC power, hydrophone, AE hit/time/source files, and continuous AE waveform data where available. Processed products include synchronized thermal and acoustic data, heat-flux/surface-temperature estimates, AE waveform features, acoustic spectra, critical-event markers, and hysteresis workbooks/tables.

**Annotations.** BoilingLab-derived. This case is saturated boiling; do not assign an MEB label. Hysteresis products are based on the measured heat-load path and should be interpreted with the pressure-adjusted reference state documented in the accompanying metadata.

**Primary tasks.** Pressure-aware heat-flux regression; post-CHF/NBR transition analysis; hysteresis-branch classification; multimodal fusion and domain-shift evaluation.

**Citation.** M. I. Hossain, Z. N. Prince, S. Pierson, C. Dunlap, A. Parjuli, and H. Hu, “Pressure-Adjusted Post-CHF Apparent Base-Wall Superheat Correlates with Boiling Hysteresis in Subatmospheric Pool Boiling,” manuscript in preparation. Cite the benchmark release as well.

## BoilingBench-3 — Ambient saturated Cu-foam pool boiling

**Data type.** Ambient saturated pool boiling on a copper-foam surface. Raw data include high-speed video, six-channel temperature, hydrophone, condenser microphone, legacy MISTRAS USB AE hit/source files, and no continuous AE WFS export. The processed package includes thermal regression products, hydrophone and microphone spectrogram/spectral features, AE hit parameters, critical-event screening markers, and clock-alignment metadata.

**Important limitations.** Pressure and DC-power files are absent in the current package; any constant pressure used by BoilingLab is a documented fallback, not a measurement. Thermocouple ordering and the effective thermal-conduction model for Cu foam require confirmation. Heat flux should therefore be treated as a screening-level derived target until geometry, conductivity, contact resistance, and calibration are verified.

**Primary tasks.** Microphone/hydrophone heat-flux regression; missing-waveform robustness; cross-surface transfer from flat Cu to Cu foam; multimodal representation learning.

**Citation and provenance.** H. Pandey, C. Li, C. Dunlap, and H. Hu, “Unveiling Hysteresis of Transient Boiling: A Multimodal Perspective,” *Applied Thermal Engineering*, 262, 125259 (2025). BoilingBench-3 is also distributed in Dryad, DOI [10.5061/dryad.ksn02v7h2](https://doi.org/10.5061/dryad.ksn02v7h2). Cite both the publication and the benchmark release.

## BoilingBench-4 — Ambient saturated flat-Cu pool boiling

**Data type.** Ambient saturated pool boiling on flat copper. Raw data include high-speed video, six-channel temperature, hydrophone, condenser microphone, legacy MISTRAS USB AE hit/source files, and no continuous AE WFS export. Processed products include thermal regression, hydrophone/microphone spectra and spectrograms, 174 AE hit records in the current analysis, critical-event screening markers, and clock-alignment metadata.

**Important limitations.** Pressure and DC-power files are absent in the current package. The four block-thermocouple coordinates were provisionally reversed in the current BoilingLab run to obtain the expected heat-flux sign; this must be confirmed against the experiment record. Heat flux is a derived screening product until the flat-Cu geometry and calibration are confirmed.

**Primary tasks.** Acoustic heat-flux regression; hydrophone versus microphone comparison; transition detection; cross-case generalization against BoilingBench-3.

**Citation and provenance.** H. Pandey, C. Li, C. Dunlap, and H. Hu, “Unveiling Hysteresis of Transient Boiling: A Multimodal Perspective,” *Applied Thermal Engineering*, 262, 125259 (2025). BoilingBench-4 is also distributed in Dryad, DOI [10.5061/dryad.ksn02v7h2](https://doi.org/10.5061/dryad.ksn02v7h2). Cite both the publication and the benchmark release.

## BoilingBench-5 — Human-annotated boiling images

**Data type.** Image-centered boiling benchmark containing RGB frames and human-created annotation files, including datasets associated with BubbleID and BubbleID-Flow. Some subdirectories also contain model checkpoints; checkpoint licensing and redistribution must be checked independently from image/annotation rights.

**Annotations.** Human annotations are the evaluation reference for bubble detection, instance/semantic segmentation, projected vapor area fraction, and morphology. Machine-generated labels must be stored separately and clearly identified.

**Primary tasks.** Bubble detection and segmentation; vapor-area-fraction regression; cross-facility domain adaptation; active learning and human-label efficiency.

**Citations.** C. Dunlap, C. Li, H. Pandey, N. Le, and H. Hu, “BubbleID: A Deep Learning Framework for Bubble Interface Dynamics Analysis,” *Journal of Applied Physics*, 136, 014902 (2024), [publisher page](https://pubs.aip.org/aip/jap/article/136/1/014902/3300686). Also cite A. Fahim et al., “BubbleID-Flow: Machine-Vision Quantification of Vapor Area Fraction in Subcooled Flow Boiling,” manuscript in preparation.

## BoilingBench-6 — Single-modality hydrophone pool boiling

**Data type.** Ambient saturated flat-copper pool-boiling reference set centered on hydrophone measurements, with associated temperature and processed acoustic-versus-heat-flux data. It is intentionally a single-modality track; do not infer unavailable pressure, video, or AE waveform channels.

**Primary tasks.** Nonintrusive acoustic heat-flux regression; hydrophone feature benchmarking; low-cost sensing and uncertainty calibration.

**Citation and provenance.** C. Dunlap, H. Pandey, E. Weems, and H. Hu, “Nonintrusive Heat Flux Quantification Using Acoustic Emissions During Pool Boiling,” *Applied Thermal Engineering*, 228, 120558 (2023), [doi:10.1016/j.applthermaleng.2023.120558](https://doi.org/10.1016/j.applthermaleng.2023.120558). The source dataset is in Dryad, DOI [10.5061/dryad.q573n5tvq](https://doi.org/10.5061/dryad.q573n5tvq).

## BoilingBench-7 — Single-modality IR immersion cooling

**Data type.** Closed immersion-cooling experiments using HFE-7100 and water, with infrared video/temperature records and electrical/thermal logs for flat devices. This is an IR-centered single-modality track, not a pool-boiling multimodal episode.

**Primary tasks.** IR temperature-field regression; thermal-event detection; fluid/device domain transfer; medium-voltage power-electronics cooling benchmarks.

**Citation and provenance.** H. Pandey, X. Du, E. Weems, S. Pierson, A. Al-Hmoud, Y. Zhao, and H. Hu, “Two-Phase Immersion Cooler for Medium-Voltage Silicon Carbide MOSFETs,” 2024 IEEE ITherm Conference, Denver, May 2024, [IEEE Xplore](https://ieeexplore.ieee.org/abstract/document/10709426). The source dataset is in Dryad, DOI [10.5061/dryad.k98sf7mk9](https://doi.org/10.5061/dryad.k98sf7mk9).

## Shared use and citation rules

Treat raw acquisition files as measured data and BoilingLab outputs as derived data. Preserve units, time bases, channel mappings, calibration metadata, processing version, and checksum. Split by run or experimental condition rather than adjacent windows. Check redistribution rights for raw files, annotations, manuscripts, and model checkpoints separately. The dataset license remains pending a rights audit; do not assume a software license covers data.
