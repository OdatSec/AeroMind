# Contributing to AeroMind

Thank you for your interest in contributing to AeroMind! This project is a
research artifact accompanying the RAID 2026 paper. We welcome contributions
that improve reproducibility, extend the evaluation, or add defensive
countermeasures.

---

## 🚀 Ways to Contribute

- **Bug reports** — open a GitHub Issue with a minimal reproduction case
- **New attack scenarios** — extend the `attacks/` framework with new threat vectors
- **New defense mechanisms** — add to `uavsys/memory/defense.py`
- **Additional LLM backends** — extend `uavsys/llm/ollama_client.py`
- **Documentation improvements** — fix typos, clarify setup steps, add examples

---

## 🛠️ Development Setup

```bash
git clone https://github.com/OdatSec/AeroMind.git
cd AeroMind
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📋 Contribution Guidelines

1. **Fork** the repository and create a feature branch: `git checkout -b feat/your-feature`
2. **Keep attack implementations** isolated in `attacks/` — never call attack code from `uavsys/`
3. **Add a named config** to `configs/baseline_configs.yaml` for any new experiment
4. **Run the baseline** (`B0`) before and after changes to confirm no regressions
5. **Open a Pull Request** with a clear description of what was changed and why

---

## ⚠️ Responsible Disclosure

If your contribution includes a new attack vector or vulnerability, please follow
responsible disclosure norms and read [SECURITY.md](SECURITY.md) before opening a PR.

---

<sub>AeroMind · RAID 2026</sub>
