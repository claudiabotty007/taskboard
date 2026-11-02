# Contributing

## Commit messages

Use `type(scope): summary` (types: feat, fix, test, build, ci, docs, chore) and add a
Jenkins directive when a change doesn't need the full matrix:

```text
docs: clarify setup steps [skip ci]          -> no build
fix(node): reject arrays in PATCH [node]      -> node backend on linux + windows
build(windows): faster zip step [windows]     -> both backends, windows only
fix(python): trim titles [python] [linux]     -> python backend, linux only
```

A change to shared code (frontend, tests, Jenkinsfile, the API contract) should run the
full matrix, so leave the directives off.

## Before pushing

```bash
./scripts/build.sh all && ./scripts/test.sh all          # Linux
```

```powershell
.\scripts\build.ps1 -Backend all; .\scripts\test.ps1 -Backend all   # Windows
```
