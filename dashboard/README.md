# BoilingBench Results Lab

Static, source-backed dashboard for the pinned public release and the two CUDA diagnostics. It publishes only small derived result files and provenance links; the full archive remains in external storage.

## Local preview

```sh
python3 -m http.server 4173 --directory dashboard
```

Then open `http://localhost:4173`.

The page intentionally shows the failed transfer cases. It should not be read as a CHF detector: the temporal target is derived heat flux, the visual target is derived polygon area fraction, and the current release does not provide confirmed event ground truth.
