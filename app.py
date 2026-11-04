"""Flagged-summary demo v2 (SIMULATION).

What a Cochrane peer reviewer would see when the checker flags a plain-language
summary (PLS). Flags are hand-set from the pilot answer key, NOT produced by a
model. Example: review CD008538 (sargramostim for Crohn's disease),
gem-cochrane-simplification-train-2129.
"""
import re
import gradio as gr

BOLD = re.compile(r"\*\*(.+?)\*\*")
DOI = "10.1002/14651858.CD008538.pub2"

# ---------------------------------------------------------------- data
SUMMARY_SENTENCES = [
    "This review of three studies did not show any difference in effectiveness between "
    "sargramostim and placebo (fake drug) for induction of remission or clinical "
    "improvement in patients with active Crohn's disease.",
    "Side effects associated with sargramostim treatment included bone pain, "
    "musculoskeletal chest pain, and dyspnea (shortness of breath).",
    "Due to the fact that there were only a small number of trials in this area and "
    "some of them give opposite results, the authors concluded that while sargramostim "
    "does not appear to be more effective than placebo more research is needed to "
    "determine if this drug provides a benefit for the treatment of active Crohn's disease.",
]

# state per abstract sentence: finding_kept | finding_dropped | context_dropped | context_kept
ABSTRACT = [
    ("Three studies were identified, 2 published as full papers and one in abstract form (537 patients).", "context_kept"),
    ("The risk of bias was low for the 3 included studies.", "context_dropped"),
    ("There was no statistically significant difference in the proportion of patients (GM-CSF 25.3% versus placebo 17.5%) who achieved clinical remission (RR 1.67; 95% CI 0.80 to 3.50; P = 0.17; 3 studies; 537 patients).", "finding_kept"),
    ("There was no statistically significant difference in the proportion of patients (GM-CSF 38.3% versus placebo 24.8%) who achieved a 100-point clinical response (RR 1.71 95% CI 0.98 to 2.97; P = 0.06; 3 studies; 537 patients).", "finding_kept"),
    ("There was no statistically significant difference in the proportion of patients (GM-CSF 54.3% versus placebo 44.2%) who achieved a 70 point clinical response (RR 1.23; 95% CI 0.83 to 1.82; P = 0.30; 1 study; 124 patients).", "finding_kept"),
    ("There was no statistically significant difference in the proportion of patients (GM-CSF 95.8% versus placebo 89.3%) who experienced at least one adverse event (RR 1.07; 95% CI 0.99 to 1.16; P = 0.08; 2 studies; 251 patients), or serious adverse events (GM-CSF 12.0% versus placebo 4.8%; RR 2.21; 95% CI 0.84 to 5.81; P = 0.11; 2 studies; 251 patients).", "finding_dropped"),
    ("The incidence of bone pain, musculoskeletal chest pain, and dyspnea were higher in patients treated with sargramostim compared to placebo.", "finding_kept"),
    ("Other adverse events commonly associated with sargramostim such as pulmonary capillary leak syndrome, pulmonary edema, heart failure, fever, and neurotoxicity were not reported in these studies.", "finding_dropped"),
    ("Sargramostim does not appear to be more effective than placebo for induction of clinical remission or clinical improvement in patients with active Crohn's disease.", "finding_kept"),
    ("However, the GRADE analysis indicates that the overall quality of the evidence for the primary (clinical remission) and secondary outcomes (clinical response) was low indicating that further research is likely to have an impact on the effect estimates.", "finding_kept"),
]

LABEL = {
    "finding_dropped": "Dropped finding (read first)",
    "context_dropped": "Dropped context (lower priority)",
}
COLORS = {LABEL["finding_dropped"]: "#f4a259", LABEL["context_dropped"]: "#c9c9c4"}

# Flags in reading order: findings first, context last.
FLAGS = [
    dict(
        n=1, idx=5, kind="Dropped finding", severity="major", match=1,
        short="Serious adverse events",
        why=(
            "**Why it matters:** serious adverse events were 12.0% vs 4.8%. The difference was "
            "not statistically significant but is still clinically important, and a patient "
            "would not learn it from this summary."
        ),
        ask=(
            "The abstract reports serious adverse events (12.0% with sargramostim vs 4.8% "
            "with placebo; not statistically significant). The summary does not mention "
            "serious adverse events. Please consider stating this."
        ),
    ),
    dict(
        n=2, idx=7, kind="Dropped finding", severity="major", match=1,
        short="Known serious harms not reported",
        why=(
            "**Why it matters:** a patient could take \"no other side effects listed\" to "
            "mean \"no other side effects exist.\""
        ),
        ask=(
            "The abstract says other known serious harms (pulmonary capillary leak syndrome, "
            "pulmonary edema, heart failure) were not reported in these studies. The summary "
            "does not say so, so its list of side effects reads as complete. Please consider "
            "adding a sentence."
        ),
    ),
    dict(
        n=3, idx=1, kind="Dropped context", severity="lower priority", match=None,
        short="Risk of bias was low",
        why=(
            "**Why it matters less:** background, not a result. It is flagged because the "
            "checker looks at every abstract sentence. Read it last. Cochrane's guidance "
            "leaves many sentences out by design."
        ),
        ask=None,
    ),
]
FLAG_BY_N = {f["n"]: f for f in FLAGS}
DECISIONS = ["Send to author team", "Dismiss", "Unsure"]

# ---------------------------------------------------------------- visuals
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8d8c86"

CSS = """
.viz {font-family: inherit; color: var(--body-text-color);}
.html-container {padding: 0 !important;}
.viz h4 {margin: 0 0 2px; font-size: 14px; font-weight: 600;}
.viz .sub {font-size: 12px; color: var(--body-text-color-subdued); margin-bottom: 12px;}
.viz .legend {display:flex; flex-wrap:wrap; gap:4px 14px; font-size:12px; margin-top:8px;
  color: var(--body-text-color-subdued);}
.viz .legend i {display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px;
  vertical-align:-1px;}
.strip {display:flex; gap:2px;}
.strip .cell {flex:1; height:40px; border-radius:2px; display:flex; align-items:center;
  justify-content:center; font-size:11px; font-weight:600; color:#fff;}
.strip .fk {background:#2a78d6;}
.strip .fd {background:#eb6834;}
.strip .cd {background: repeating-linear-gradient(45deg,#8d8c86,#8d8c86 3px,#b9b8b2 3px,#b9b8b2 6px);}
.strip .ck {background: transparent; border:1.5px solid #8d8c86; color: var(--body-text-color-subdued);}
.stack {display:flex; gap:2px; height:40px;}
.stack .seg {display:flex; align-items:center; justify-content:center; color:#fff;
  font-size:12px; font-weight:600; border-radius:2px;}
.viz.card {height:100%; box-sizing:border-box;}
.card {border:1px solid var(--border-color-primary); border-radius:8px; padding:12px 14px;
  background: var(--background-fill-secondary);}
.sumtext {line-height:1.6; font-size:15px;}
.sumtext mark {background: rgba(235,104,52,.25); color: inherit; padding:1px 2px; border-radius:3px;}
.pair {border-left:3px solid #eb6834; padding:4px 10px; margin:6px 0; font-size:14px;
  background: var(--background-fill-primary);}
.pair.sum {border-left-color:#2a78d6;}
.pair small {display:block; color: var(--body-text-color-subdued); font-size:11px;
  text-transform:uppercase; letter-spacing:.04em; margin-bottom:2px;}
.verdict {font-size:16px; padding:10px 14px; border-radius:8px; border:1px solid #eb6834;
  background: rgba(235,104,52,.10);}
"""


def strip_html():
    cls = {"finding_kept": "fk", "finding_dropped": "fd", "context_dropped": "cd", "context_kept": "ck"}
    cells = "".join(f'<div class="cell {cls[s]}" title="Sentence {i+1}">{i+1}</div>' for i, (_, s) in enumerate(ABSTRACT))
    n_flag = sum(1 for _, s in ABSTRACT if s.endswith("dropped"))
    return f"""<div class="viz card">
<h4>Where the flags are: {n_flag} of {len(ABSTRACT)} abstract sentences</h4>
<div class="sub">Each box is one abstract sentence, in order.</div>
<div class="strip">{cells}</div>
<div class="legend"><span><i style="background:{BLUE}"></i>Finding, kept</span>
<span><i style="background:{ORANGE}"></i>Finding, dropped</span>
<span><i style="background:repeating-linear-gradient(45deg,#8d8c86,#8d8c86 2px,#b9b8b2 2px,#b9b8b2 4px)"></i>Context, dropped</span>
<span><i style="border:1.5px solid #8d8c86"></i>Context, kept</span></div></div>"""


def coverage_html():
    kept = sum(1 for _, s in ABSTRACT if s == "finding_kept")
    dropped = sum(1 for _, s in ABSTRACT if s == "finding_dropped")
    total = kept + dropped
    return f"""<div class="viz card">
<h4>Findings carried into the summary: {kept} of {total}</h4>
<div class="sub">Only findings count here, not background sentences.</div>
<div class="stack">
<div class="seg" style="flex:{kept};background:{BLUE}">{kept} kept</div>
<div class="seg" style="flex:{dropped};background:{ORANGE}">{dropped} dropped</div></div>
<div class="legend"><span>Partly kept: 0 (would count as dropped)</span></div></div>"""


def summary_html(match):
    parts = []
    for i, s in enumerate(SUMMARY_SENTENCES):
        parts.append(f"<mark>{s}</mark>" if i == match else s)
    return f'<div class="card sumtext">{" ".join(parts)}</div>'


def detail_html(n):
    f = FLAG_BY_N[n]
    abs_sent = ABSTRACT[f["idx"]][0]
    if f["match"] is None:
        closest = "<em>No close match in the summary.</em>"
    else:
        closest = SUMMARY_SENTENCES[f["match"]]
    why_html = BOLD.sub(r"<b>\1</b>", f["why"])
    return f"""<div class="card">
<div style="font-weight:600;margin-bottom:6px">Flag {n} of 3 · {f['kind']} ({f['severity']}) · {f['short']}</div>
<div class="pair"><small>Abstract says</small>{abs_sent}</div>
<div class="pair sum"><small>Closest summary sentence (highlighted on the left)</small>{closest}</div>
<div style="margin-top:8px;font-size:14px;line-height:1.55">{why_html}</div></div>"""


# ---------------------------------------------------------------- handlers
def choose_flag(n):
    n = int(n)
    return summary_html(FLAG_BY_N[n]["match"]), detail_html(n)


def save_decision(n, choice, state):
    state = dict(state)
    if choice:
        state[int(n)] = choice
    done = len(state)
    return state, f"Decisions made: {done} of {len(FLAGS)}"


def load_decision(n, state):
    return state.get(int(n))


def toggle_abstract(show):
    return gr.update(visible=show)


def export_note(state):
    sent = [f for f in FLAGS if state.get(f["n"]) == "Send to author team" and f["ask"]]
    if not sent:
        return "No flags marked \"Send to author team\" yet."
    lines = [
        f"Hello author team,\n\nThank you for the draft of the plain-language summary for "
        f"Cochrane review {DOI}. While comparing it with the abstract, I found content that "
        f"may have been dropped:\n"
    ]
    for i, f in enumerate(sent, 1):
        lines.append(f"{i}. {f['ask']}")
    lines.append("\nCould you review these before publication?\n\nThank you.")
    return "\n".join(lines)


def full_abstract_value():
    return [(s + " ", LABEL[k] if k in LABEL else None) for s, k in ABSTRACT]


# ---------------------------------------------------------------- app
with gr.Blocks(title="Flagged summary demo") as demo:
    state = gr.State({})
    gr.Markdown(
        "# Flagged summary: reviewer view\n"
        f"Cochrane review [{DOI}](https://doi.org/{DOI}) · sargramostim for active Crohn's disease"
    )
    gr.Markdown(
        "**This is a simulation.** Flags are hand-set from a pilot answer key to show the "
        "layout. No model produced them, and the cut-off is not set yet."
    )
    gr.HTML('<div class="viz verdict"><b>3 flags to review:</b> 2 dropped findings (both about harms) '
            'and 1 dropped context sentence. Start with flag 1.</div>')
    with gr.Row(equal_height=True):
        with gr.Column(scale=3):
            gr.HTML(strip_html())
        with gr.Column(scale=2):
            gr.HTML(coverage_html())

    with gr.Row(equal_height=False):
        with gr.Column(scale=1):
            gr.Markdown("### Plain-language summary (written by the author team)")
            summary = gr.HTML(summary_html(FLAGS[0]["match"]))
            show_full = gr.Checkbox(label="Show the full abstract", value=False)
            full_abs = gr.HighlightedText(
                value=full_abstract_value(), color_map=COLORS, show_legend=True,
                combine_adjacent=False, interactive=False, show_label=False, visible=False,
            )
        with gr.Column(scale=1):
            gr.Markdown("### Flags to review, in reading order")
            flag_pick = gr.Radio(
                choices=[(f"{f['n']} · {f['kind']}: {f['short']}", f["n"]) for f in FLAGS],
                value=1, show_label=False,
            )
            detail = gr.HTML(detail_html(1))
            decision = gr.Radio(DECISIONS, label="Your decision on this flag")
            progress = gr.Markdown("Decisions made: 0 of 3")

    export_btn = gr.Button("Draft note to author team", variant="primary")
    note = gr.Textbox(label="Draft note (edit before sending)", lines=8, interactive=True)

    flag_pick.change(choose_flag, flag_pick, [summary, detail])
    flag_pick.change(load_decision, [flag_pick, state], decision)
    decision.input(save_decision, [flag_pick, decision, state], [state, progress])
    export_btn.click(export_note, state, note)
    show_full.change(toggle_abstract, show_full, full_abs)

if __name__ == "__main__":
    demo.launch(css=CSS)
