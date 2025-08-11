# AGENTS.md — How ChatGPT/Codex should work with this repo

This file is non-normative. It complements the existing docs (keep them unchanged):
- **AFPSNN-MANIFEST.md** (normative spec, v0.3.6)
- **API-INTERFACES.md** (shapes/ABI)
- **SPRINT-01.md** (acceptance)
- **README-SESSION-PRIMER.md** (ritual for normal ChatGPT sessions)
- **README-BOOTSTRAP.md** (human quickstart)

## Agent operating rules (ChatGPT/Codex in the cloud)
1) **Do not run GPU benches.** Assume CPU-only.
2) Use the **smoke path** to validate changes quickly:
   - `./scripts/codex.setup.sh`
   - `make smoke`
   - `pytest -q`
3) If a GPU validation is needed, **open a PR** and rely on the **GPU CI workflow** (/.github/workflows/gpu-tests.yml) which runs on a self-hosted GPU runner.

## Fast tasks
### Sprint-01 smoke
```
./scripts/codex.setup.sh
make smoke
pytest -q
```
### Static checks (optional if tools are present)
```
make lint || true
make format || true
```

## Notes for the agent
- Keep deterministic settings on the smoke config.
- Do not modify MANIFEST/API/SPRINT unless explicitly asked (spec bump needed).
- If CUDA is unavailable, `codex.setup.sh` will skip the kernel build and continue.
