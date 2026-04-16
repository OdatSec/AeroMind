# Security Policy

## Supported Versions

AeroMind is a **research artifact** released alongside the RAID 2026 paper. The
`main` branch is the only maintained version.

| Version | Maintained |
|---|:---:|
| `main` | ✅ |

---

## ⚠️ Scope & Intended Use

**AeroMind is a security research testbed. The attack scenarios implemented here
are intentional and disclosed as part of responsible academic research.**

This artifact is designed **exclusively** for use in:
- Isolated PX4 Software-In-The-Loop (SITL) simulation environments
- Controlled research infrastructure with no connection to live airspace
- Academic and defensive security research

### Strictly prohibited uses

- Deployment against real UAV hardware or operational drones
- Use in live airspace or shared network infrastructure
- Use against systems you do not own or have explicit written authorization to test
- Any use that may endanger persons, property, or aviation safety

---

## 🔍 Reporting Vulnerabilities

The attack vulnerabilities documented in this codebase are **deliberately
implemented** and already disclosed via the RAID 2026 publication. If you
discover an **unintentional** vulnerability in the artifact infrastructure itself
(not in the intentional attack scenarios), please report it responsibly:

**Do not open a public GitHub Issue for undisclosed vulnerabilities.**

Instead, contact the authors directly via encrypted email or GitHub's private
security advisory feature:

| Contact | Email |
|---|---|
| Ibrahim Odat (primary) | ibrahimodat@oakland.edu |
| Anyi Liu | anyiliu@oakland.edu |
| Yingjiu Li | yingjiul@uoregon.edu |

We aim to respond to all security reports within **72 hours** and will
coordinate disclosure timelines with the reporter.

---

## 🧪 Responsible Research Guidelines

By cloning, forking, or otherwise using this repository, you agree to:

1. **Simulation only** — run all experiments in isolated PX4 SITL; never on real hardware
2. **No harm** — do not use any attack scenario to disrupt, damage, or deny service to any real system
3. **Attribution** — cite the RAID 2026 paper in any derivative work (see [`CITATION.cff`](CITATION.cff))
4. **Disclosure** — if you build upon or extend these attack scenarios, follow responsible disclosure norms before publishing

---

<sub>AeroMind · RAID 2026 · Oakland University & University of Oregon</sub>
