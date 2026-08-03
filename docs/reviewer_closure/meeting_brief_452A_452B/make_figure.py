"""Per-reviewer charts for the meeting brief. One standalone chart per closed gap, placed
directly beneath its section in the brief. Values are transcribed EXACTLY from the curated
closure artifacts (no recomputation, no invented numbers):
  figA  452A_part1  saturated_per_profile.csv + nonsaturated_per_profile_budget.csv
  figB  452A_part2  fleet_by_assignment.csv
  figC  452B-1      plan_per_cell.csv (adoption + CI) and ret_per_cell.csv (CCR series)
Also emits the combined 3-panel figure.pdf/png for reference.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.titleweight": "bold",
                     "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 200})


def panel_A(ax):
    profiles = ["Sparse\n(3)", "Operational\n(60)", "Dense\n(200)", "Episodic\n(60)", "Benign-sim\n(60)"]
    x = range(len(profiles))
    ax.plot(x, [1.0] * 5, "o-", color="#b2182b", label="budget 3")       # saturated CSV
    ax.plot(x, [0.6667] * 5, "s-", color="#ef8a62", label="budget 2")    # nonsaturated CSV
    ax.plot(x, [0.3333] * 5, "^-", color="#67a9cf", label="budget 1")
    ax.set_xticks(list(x)); ax.set_xticklabels(profiles, fontsize=9.5)
    ax.set_ylim(0, 1.08); ax.set_ylabel("Retrieval contamination (CCR)")
    ax.set_title("452A-1  —  Memory generalization")
    ax.legend(fontsize=9.5, loc="center right", framealpha=0.9)


def panel_B(ax):
    agents = [3, 5, 9, 17]                    # fleet_by_assignment.csv total_agents
    blast = [3, 5, 9, 17]                     # blast_count_mean (identical for all 3 policies)
    ax.plot(agents, blast, "o-", color="#b2182b", markersize=10, label="fixed")
    ax.plot(agents, blast, "s--", color="#762a83", markersize=6.5, label="random")
    ax.plot(agents, blast, "^:", color="#1b7837", markersize=5, label="dynamic")
    ax.plot(agents, [0, 0, 0, 0], "x-", color="#4d4d4d", label="A00 control")
    for xa, yb in zip(agents, blast):
        ax.annotate(str(yb), (xa, yb), textcoords="offset points", xytext=(-13, 4), fontsize=9.5)
    ax.set_xticks(agents); ax.set_xlabel("Total agents in fleet")
    ax.set_ylabel("Agents exposed (blast count)")
    ax.set_ylim(-1, 18); ax.set_title("452A-2  —  Agent / task scalability")
    ax.legend(fontsize=9.5, loc="upper left", framealpha=0.9)


def panel_C(ax):
    k = [3, 5, 10, 20]; xc = list(range(len(k)))
    adopt = [1.0, 0.4, 0.6, 0.1]              # plan_per_cell.csv adopt_valid_mean
    lo = [1.0, 0.1, 0.3, 0.0]; hi = [1.0, 0.7, 0.9, 0.3]
    yerr = [[a - l for a, l in zip(adopt, lo)], [h - a for a, h in zip(adopt, hi)]]
    ccr = [1.0, 0.6, 0.3, 0.15]               # ret_per_cell.csv sym CCR at budget 3
    ax.errorbar(xc, adopt, yerr=yerr, fmt="o-", color="#2166ac", capsize=4,
                markersize=9, label="planner adoption (95% CI)")
    ax.plot(xc, ccr, "d--", color="#999999", label="retrieval CCR (budget 3)")
    ax.set_xticks(xc); ax.set_xticklabels([str(v) for v in k]); ax.set_xlim(-0.3, 3.3)
    ax.set_xlabel("Planner retrieval depth  k"); ax.set_ylabel("Rate"); ax.set_ylim(-0.05, 1.1)
    ax.set_title("452B-1  —  Top-k saturation & adoption")
    ax.legend(fontsize=9.5, loc="upper right", framealpha=0.9)


def save_single(fn, panel, size):
    fig, ax = plt.subplots(figsize=size)
    panel(ax); fig.tight_layout()
    fig.savefig(os.path.join(HERE, fn + ".pdf")); fig.savefig(os.path.join(HERE, fn + ".png"), dpi=200)
    plt.close(fig)


save_single("figA", panel_A, (7.4, 4.3))
save_single("figB", panel_B, (7.4, 4.3))
save_single("figC", panel_C, (7.4, 4.3))

# combined reference figure
figc, axs = plt.subplots(1, 3, figsize=(13.2, 4.3))
panel_A(axs[0]); panel_B(axs[1]); panel_C(axs[2])
figc.tight_layout(); figc.savefig(os.path.join(HERE, "figure.pdf"))
figc.savefig(os.path.join(HERE, "figure.png"), dpi=200); plt.close(figc)
print("wrote figA/figB/figC (.pdf/.png) and combined figure.pdf/png")
