from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Mycelial_Graph_V1_Research_Edition.pdf"

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#1F6FEB")
GREEN = colors.HexColor("#2F855A")
MINT = colors.HexColor("#DFF6EA")
ICE = colors.HexColor("#EAF2FF")
AMBER = colors.HexColor("#F6AD55")
INK = colors.HexColor("#243B53")
MUTED = colors.HexColor("#627D98")
LIGHT = colors.HexColor("#F5F7FA")
WHITE = colors.white


def register_fonts() -> tuple[str, str, str]:
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    mono = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    if regular.exists() and bold.exists() and mono.exists():
        pdfmetrics.registerFont(TTFont("MGRegular", regular))
        pdfmetrics.registerFont(TTFont("MGBold", bold))
        pdfmetrics.registerFont(TTFont("MGMono", mono))
        return "MGRegular", "MGBold", "MGMono"
    return "Helvetica", "Helvetica-Bold", "Courier"


REGULAR, BOLD, MONO = register_fonts()


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName=BOLD,
            fontSize=29,
            leading=34,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            fontName=REGULAR,
            fontSize=13,
            leading=19,
            textColor=colors.HexColor("#D9E8FF"),
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName=BOLD,
            fontSize=19,
            leading=23,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=11,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName=BOLD,
            fontSize=12.5,
            leading=16,
            textColor=GREEN,
            spaceBefore=9,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=REGULAR,
            fontSize=9.4,
            leading=14.1,
            textColor=INK,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName=REGULAR,
            fontSize=7.8,
            leading=11.2,
            textColor=MUTED,
        ),
        "callout": ParagraphStyle(
            "Callout",
            fontName=BOLD,
            fontSize=11.5,
            leading=16,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "code": ParagraphStyle(
            "Code",
            fontName=MONO,
            fontSize=7.8,
            leading=11.2,
            textColor=NAVY,
            backColor=LIGHT,
            borderPadding=8,
            borderColor=colors.HexColor("#CBD5E0"),
            borderWidth=0.5,
            borderRadius=3,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "table": ParagraphStyle(
            "Table",
            fontName=REGULAR,
            fontSize=7.2,
            leading=9.5,
            textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            fontName=BOLD,
            fontSize=7.2,
            leading=9.5,
            textColor=WHITE,
        ),
    }


S = styles()


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"<font color='#2F855A'>•</font> {text}", S["body"])


def table(rows, widths, header=True):
    rendered = []
    for row_index, row in enumerate(rows):
        style = "table_head" if header and row_index == 0 else "table"
        rendered.append([P(str(cell), style) for cell in row])
    result = Table(rendered, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY if header else WHITE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return result


def architecture_drawing() -> Drawing:
    d = Drawing(475, 205)
    layers = [
        (55, [102], "Task"),
        (145, [64, 102, 140], "Prompt"),
        (245, [64, 102, 140], "Retriever"),
        (345, [64, 102, 140], "Model"),
        (435, [102], "Output"),
    ]
    for index in range(len(layers) - 1):
        x1, ys1, _ = layers[index]
        x2, ys2, _ = layers[index + 1]
        for y1 in ys1:
            for y2 in ys2:
                d.add(Line(x1 + 12, y1, x2 - 12, y2, strokeColor=colors.HexColor("#9FB3C8"), strokeWidth=0.65))
    for x, ys, label in layers:
        for y in ys:
            d.add(Circle(x, y, 11, fillColor=MINT if len(ys) > 1 else ICE, strokeColor=GREEN, strokeWidth=1.3))
        d.add(String(x, 26, label, textAnchor="middle", fontName=BOLD, fontSize=7.5, fillColor=NAVY))
    d.add(Rect(116, 170, 243, 25, rx=5, ry=5, fillColor=ICE, strokeColor=BLUE, strokeWidth=0.8))
    d.add(String(237.5, 179, "Immutable scenario + local feedback contract", textAnchor="middle", fontName=BOLD, fontSize=8.2, fillColor=NAVY))
    return d


def shock_drawing() -> Drawing:
    d = Drawing(470, 150)
    d.add(Rect(12, 15, 135, 110, rx=7, ry=7, fillColor=ICE, strokeColor=BLUE))
    d.add(Rect(168, 15, 135, 110, rx=7, ry=7, fillColor=MINT, strokeColor=GREEN))
    d.add(Rect(324, 15, 135, 110, rx=7, ry=7, fillColor=colors.HexColor("#FFF4E5"), strokeColor=AMBER))
    d.add(String(79, 105, "rho = 0", textAnchor="middle", fontName=BOLD, fontSize=11, fillColor=NAVY))
    d.add(String(235, 105, "rho = 0.5", textAnchor="middle", fontName=BOLD, fontSize=11, fillColor=NAVY))
    d.add(String(391, 105, "rho = 1", textAnchor="middle", fontName=BOLD, fontSize=11, fillColor=NAVY))
    d.add(String(79, 73, "edge-specific", textAnchor="middle", fontName=REGULAR, fontSize=9, fillColor=INK))
    d.add(String(235, 73, "mixed", textAnchor="middle", fontName=REGULAR, fontSize=9, fillColor=INK))
    d.add(String(391, 73, "node-shared", textAnchor="middle", fontName=REGULAR, fontSize=9, fillColor=INK))
    d.add(String(79, 42, "negative-transfer control", textAnchor="middle", fontName=REGULAR, fontSize=7.5, fillColor=MUTED))
    d.add(String(235, 42, "primary contrast", textAnchor="middle", fontName=REGULAR, fontSize=7.5, fillColor=MUTED))
    d.add(String(391, 42, "positive diagnostic", textAnchor="middle", fontName=REGULAR, fontSize=7.5, fillColor=MUTED))
    d.add(String(235, 2, "Total L2 shock magnitude remains constant", textAnchor="middle", fontName=BOLD, fontSize=8.5, fillColor=GREEN))
    return d


def lifecycle_drawing() -> Drawing:
    d = Drawing(470, 115)
    xs = [40, 145, 250, 355, 445]
    labels = ["Develop", "Pilot", "Fix N", "Confirm", "Decide"]
    subtitles = ["debug only", "variance", "addendum", "no tuning", "gate"]
    for index, (x, label, subtitle) in enumerate(zip(xs, labels, subtitles)):
        if index < len(xs) - 1:
            d.add(Line(x + 23, 65, xs[index + 1] - 23, 65, strokeColor=BLUE, strokeWidth=2))
            d.add(Polygon([xs[index + 1] - 27, 69, xs[index + 1] - 20, 65, xs[index + 1] - 27, 61], fillColor=BLUE, strokeColor=BLUE))
        d.add(Circle(x, 65, 23, fillColor=MINT if index != 3 else ICE, strokeColor=GREEN if index != 3 else BLUE, strokeWidth=1.5))
        d.add(String(x, 61, str(index + 1), textAnchor="middle", fontName=BOLD, fontSize=11, fillColor=NAVY))
        d.add(String(x, 29, label, textAnchor="middle", fontName=BOLD, fontSize=8.5, fillColor=NAVY))
        d.add(String(x, 16, subtitle, textAnchor="middle", fontName=REGULAR, fontSize=7, fillColor=MUTED))
    return d


class MGDocument(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=0.68 * inch,
            rightMargin=0.68 * inch,
            topMargin=0.68 * inch,
            bottomMargin=0.62 * inch,
            title="Mycelial Graph V1 Research Edition",
            author="Crizan Belem Ribeiro",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self._page))

    def _page(self, canvas, doc):
        if doc.page == 1:
            canvas.saveState()
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, letter[0], letter[1], stroke=0, fill=1)
            canvas.setFillColor(GREEN)
            canvas.circle(525, 700, 110, stroke=0, fill=1)
            canvas.setFillColor(colors.HexColor("#194C5B"))
            canvas.circle(65, 85, 150, stroke=0, fill=1)
            canvas.restoreState()
            return
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
        canvas.line(0.68 * inch, 0.48 * inch, letter[0] - 0.68 * inch, 0.48 * inch)
        canvas.setFont(REGULAR, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.68 * inch, 0.29 * inch, "MYCELIAL GRAPH V1 RESEARCH EDITION")
        canvas.drawRightString(letter[0] - 0.68 * inch, 0.29 * inch, f"{doc.page}")
        canvas.restoreState()


def build_story():
    story = [
        Spacer(1, 1.65 * inch),
        P("MYCELIAL GRAPH V1", "title"),
        P("Research Edition", "title"),
        Spacer(1, 0.08 * inch),
        P("Architecture, frozen experimental protocol, demonstrable POC, and evidence-gated evolution plan", "subtitle"),
        Spacer(1, 0.46 * inch),
        P("Crizan Belem Ribeiro", "subtitle"),
        P("Independent Researcher | Sao Paulo, Brazil", "subtitle"),
        Spacer(1, 1.65 * inch),
        P("VERSION 0.1.0  |  MG-EXP-V1  |  AUGUST 2026", "small"),
        PageBreak(),
        P("Executive overview", "h1"),
        P("Mycelial Graph is a research framework for adaptive routing across heterogeneous AI execution components. Its motivating idea is simple: when a local provider, model, retriever, tool, or cloud component degrades, the system should update the affected region while preserving useful state elsewhere."),
        architecture_drawing(),
        P("The biological metaphor provides design intuition, not proof. V1 converts it into a falsifiable experiment: hierarchical node-edge state should recover with fewer observations when a shock is shared through a node, but it must not create unacceptable negative transfer when a disruption belongs to one edge."),
        Spacer(1, 4),
        Table(
            [[P("What V1 is", "callout"), P("What V1 is not", "callout")],
             [P("A local, reproducible simulator with frozen paired scenarios, four methods, paired analysis, automatic reporting, and a locked confirmatory workflow."),
              P("A production multicloud router, a proof of convergence, a provider benchmark, or evidence that hierarchy is already superior.")]],
            colWidths=[3.25 * inch, 3.25 * inch],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), MINT),
                ("BACKGROUND", (1, 0), (1, -1), ICE),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#9FB3C8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ])
        ),
        PageBreak(),
        P("1. The original idea, preserved", "h1"),
        P("Production AI systems are graphs, even when their code looks like a linear pipeline. A task can select among prompt strategies, retrieval services, models, tools, guardrails, parsers, regions, and fallbacks. Costs, latency, quality, quotas, and availability change independently."),
        P("The V0 contribution was an adaptive edge conductance: useful local flow reinforces a connection; inactivity and changing evidence allow it to decay. V1 keeps this mechanism intact as the <b>edge-only control</b>. The project does not replace its core idea with generic reinforcement learning, a graph neural network, or a large orchestrator."),
        P("V1 adds one candidate mechanism: partial pooling through node state. This is a scientific extension, not a declared product upgrade."),
        P("Core invariant", "h2"),
        Table([[P("LOCAL ADAPTATION + STRUCTURAL REUSE + HARD EVIDENCE BOUNDARIES", "callout")]], colWidths=[6.5 * inch], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), MINT), ("BOX", (0, 0), (-1, -1), 0.8, GREEN), ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14)])),
        P("Product objective", "h2"),
        P("Minimize cost per successful task while preserving explicit quality, latency, reliability, safety, and policy requirements. Token price alone is never the optimization target."),
        P("Scientific objective", "h2"),
        P("Measure whether the recovery burden changes as the true shared fraction of a localized shock changes, and identify when sharing becomes harmful."),
        P("Engineering objective", "h2"),
        P("Create a small local package that can later accept frozen real-provider traces and bounded live adapters without rewriting its experimental core."),
        PageBreak(),
        P("2. The research architecture", "h1"),
        P("Each module has one responsibility. The environment produces an immutable world. Methods choose and update using only permitted local feedback. The runner pairs results. Analysis consumes raw records but cannot change them."),
        table([
            ["Layer", "Responsibility", "Invariant"],
            ["Configuration", "Frozen graph, horizon, shock, methods, metrics, and seeds", "YAML is the single scientific source of truth"],
            ["Environment", "DAG, latent means, indexed potential outcomes, certified optima", "Read-only after generation"],
            ["Methods", "Choose a path and update local state", "Same observation contract; isolated RNG"],
            ["Runner", "Execute paired scenarios, traces, and checkpoints", "Atomic, idempotent, serial/parallel equivalent"],
            ["Analysis", "RRT, RMST estimate, regret, bootstrap, gates", "No tuning or seed filtering"],
            ["Reporting", "Tables, figures, interpretation boundary", "Run kind always visible"],
        ], [1.0 * inch, 3.2 * inch, 2.3 * inch]),
        P("Immutable scenario contract", "h2"),
        P("Potential outcomes are indexed by step and edge. If two methods choose the same edge at the same time, they receive the same local noise realization. Different actions query different outcomes from the same frozen world. This is stronger than reusing one mutable RNG sequence."),
        P("Randomness", "h2"),
        P("Stable namespaces derive independent streams for scenario parameters, local outcome noise, and each method. Completion order under ProcessPoolExecutor cannot change the canonical scientific payload."),
        PageBreak(),
        P("3. Controlled structural sharing", "h1"),
        shock_drawing(),
        P("The experiment constructs orthogonal node and interaction shock patterns. The parameter rho reallocates squared shock magnitude between them while total L2 magnitude remains fixed."),
        P("d(rho) = -m [ sqrt(rho) n + sqrt(1-rho) i ]", "code"),
        P("For each seed, all rho values share the same graph, pre-shock edge means, and potential-noise table. A candidate family is admitted only when every configured rho has a changed, unique post-shock optimum with the minimum utility margin."),
        P("Why the endpoints matter", "h2"),
        bullet("rho=0 is the negative-transfer control: a hierarchy that broadcasts an edge-specific observation can hurt."),
        bullet("rho=1 is the positive diagnostic: fully shared node information is the most favorable pooling regime."),
        bullet("rho=0.5 is the primary mixed regime: shared and specific components contribute equally in squared magnitude."),
        P("What methods observe", "h2"),
        P("Methods receive local rewards only for traversed edges. Expected utility, shock location, future outcomes, and oracle paths remain evaluation-only information."),
        PageBreak(),
        P("4. Methods and fair comparison", "h1"),
        table([
            ["Method", "State", "Selection", "Scientific role"],
            ["MG edge-only", "Independent bounded edge conductance", "Softmax + basal exploration", "Preserves the V0 mechanism"],
            ["Node-only", "Source and target node effects", "Same MG policy family", "Pooling ablation"],
            ["MG hierarchical", "Source + target + edge interaction", "Same MG policy family", "Proposed partial pooling"],
            ["Structured SW-UCB", "The same node-edge feature family", "Sliding-window UCB", "Strong representation-aware baseline"],
        ], [1.18 * inch, 1.85 * inch, 1.45 * inch, 2.02 * inch]),
        P("Hierarchical score", "h2"),
        P("score(u,v,t) = base + a[u,t] + b[v,t] + c[u,v,t]", "code"),
        P("Online updates use sum-to-zero projection and shrinkage. These constraints make the numerical parameterization reproducible, but they do not manufacture evidence for rarely observed components."),
        P("Why SW-UCB is mandatory", "h2"),
        P("Without a baseline that uses the same shared features, a hierarchical victory could be attributed only to representation. SW-UCB helps distinguish representation value from the specific Mycelial policy dynamics."),
        P("Oracle boundary", "h2"),
        P("The oracle knows expected utilities and defines the optimum. It does not compete, receive confidence intervals, or represent a deployable method. Its realized reward need not beat every stochastic draw."),
        PageBreak(),
        P("5. Recovery and decision gates", "h1"),
        P("Recovery is not one lucky optimal choice. It requires a trailing mean of expected selected-path utility to reach at least 90% of the post-shock oracle and remain there through a confirmation window."),
        P("RRT_i = min(T_recovery_i, tau)", "code"),
        P("The mean individual RRT estimates restricted mean time without recovery when censoring is administrative at tau. Lower is better."),
        P("Primary relative effect", "h2"),
        P("delta = [ E(RRT_hierarchical) - E(RRT_edge-only) ] / E(RRT_edge-only)", "code"),
        table([
            ["Gate", "Frozen rule", "Meaning"],
            ["Superiority", "95% one-sided upper bound < 0 at rho=0.5", "Evidence of lower recovery burden"],
            ["Engineering value", "Point estimate <= -20%", "Benefit may justify added complexity"],
            ["Negative-transfer safety", "Upper bound < +10% at rho=0", "No unacceptable edge-specific harm"],
            ["Promotion", "All scientific gates + operational cost budget", "Hierarchy may advance to product POC"],
        ], [1.35 * inch, 2.65 * inch, 2.5 * inch]),
        P("A non-significant result is inconclusive unless the experiment had enough power to exclude the relevant benefit. Pilot and development gates are diagnostic only."),
        PageBreak(),
        P("6. Reproducible execution lifecycle", "h1"),
        lifecycle_drawing(),
        P("The confirmatory YAML deliberately references a seed file that does not yet exist. After the pilot, the sample-size calculation is recorded in an addendum and the first N seeds are copied mechanically from a precommitted 500-seed pool."),
        P("Required artifacts", "h2"),
        table([
            ["Artifact", "Purpose"],
            ["EXPERIMENT_PROTOCOL_V1.md", "Frozen hypotheses, observation contract, metrics, gates, and prohibitions"],
            ["ANALYSIS_PLAN.md", "Estimand, paired bootstrap, censoring, multiplicity, and reporting"],
            ["SAMPLE_SIZE_ADDENDUM.md", "Pilot variance, power method, N, dates, and selected seed range"],
            ["experiment.schema.json", "Machine-readable paired result contract"],
            ["manifest.json", "Config, seed, code, dependency, and artifact hashes"],
            ["REPORT.md", "Automatic result and interpretation boundary"],
        ], [2.15 * inch, 4.35 * inch]),
        P("Checkpoint behavior", "h2"),
        P("Completed checkpoints are reused only when seed, rho, config hash, and code revision agree. A conflicting output is never silently overwritten. Traces use atomic temporary-file replacement."),
        PageBreak(),
        P("7. Sustainable project design", "h1"),
        P("Sustainability means keeping the project scientifically honest, technically maintainable, financially bounded, and computationally proportionate."),
        table([
            ["Dimension", "V1 commitment"],
            ["Scientific", "Immutable raw data, disjoint phases, amendments, and explicit negative-result paths"],
            ["Technical", "Typed small modules, local files, no database/cloud/orchestrator dependency"],
            ["Financial", "Synthetic evidence before paid calls; one-cloud canary before multicloud"],
            ["Computational", "Power-justified N, parallel local trials, idempotent checkpoints, CPU reporting"],
            ["Governance", "Cost optimization never overrides hard safety, privacy, or compliance constraints"],
        ], [1.35 * inch, 5.15 * inch]),
        P("Why there is no orchestrator yet", "h2"),
        P("Independent trials map cleanly to ProcessPoolExecutor. An external workflow engine becomes justified only when local duration, multi-node compute, dependency complexity, or infrastructure recovery becomes a measured bottleneck."),
        P("Why there is no SQLite yet", "h2"),
        P("Twenty to a few hundred paired scenarios remain transparent as JSON plus compressed traces. A database adds value only when cross-version querying becomes a repeated requirement."),
        P("Why there are no live prices", "h2"),
        P("Provider values are temporally unstable. Future real-world work must capture dated immutable traces before replay; live queries during a confirmatory run would break reproducibility."),
        PageBreak(),
        P("8. Evidence-gated evolution", "h1"),
        table([
            ["Stage", "Question", "Deliverable", "Advance only if"],
            ["V1 research", "Does partial pooling help under shared shocks?", "Confirmatory report", "Scientific gates are evaluated"],
            ["Single-cloud POC", "Does the effect survive realistic traces and bounded calls?", "Cost/quality/latency case", "V1 supports a useful regime"],
            ["Composite pipeline", "Does graph routing help beyond model choice?", "Retriever/tool/guardrail POC", "Single-cloud value is measured"],
            ["Multicloud fabric", "Does distribution solve a real resilience or sovereignty need?", "Governed execution platform", "One cloud is demonstrably insufficient"],
        ], [1.05 * inch, 2.0 * inch, 1.65 * inch, 1.8 * inch]),
        P("First cloud selection", "h2"),
        bullet("Prefer credits, low setup cost, version pinning, observable telemetry, and strict budgets."),
        bullet("Require at least two meaningful routing alternatives behind one narrow task contract."),
        bullet("Replay frozen traces locally before any live canary."),
        bullet("Measure cost per successful task, quality, p95 latency, failure rate, and recovery."),
        P("Deferred research", "h2"),
        P("Dynamic graph discovery, distributed consensus, causal attribution, counterfactual explanations, 10,000-node scaling, and formal regret bounds remain valid future questions. None is required to answer MG-EXP-V1."),
        PageBreak(),
        P("9. Demonstrable POC and current status", "h1"),
        P("The repository includes an end-to-end development command that validates configuration, generates paired scenarios, executes all four methods, calculates paired metrics, creates plots, writes a manifest, and produces a final Markdown report."),
        P("Windows PowerShell", "h2"),
        P("python -m venv .venv<br/>Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned<br/>&amp; .\\.venv\\Scripts\\Activate.ps1<br/>python -m pip install -e .<br/>mycelial-graph demo", "code"),
        P("Output contract", "h2"),
        P("outputs/demo/<br/>  raw/ - paired immutable scenario files<br/>  traces/ - compressed step decisions and selected scores<br/>  processed/analysis.json - aggregate estimates and gates<br/>  figures/ - recovery and regret plots<br/>  manifest.json - environment and hashes<br/>  REPORT.md - final human-readable result", "code"),
        P("Evidence status", "h2"),
        Table([[P("DEVELOPMENT-ONLY", "callout")], [P("The included output verifies execution and can falsify naive expectations, but it is not a confirmatory scientific result. The confirmatory configuration remains locked until the independent pilot determines N.")]], colWidths=[6.5 * inch], style=TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF4E5")), ("BACKGROUND", (0, 1), (-1, -1), WHITE), ("BOX", (0, 0), (-1, -1), 0.8, AMBER), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12)])),
        PageBreak(),
        P("10. Definition of done", "h1"),
        P("V1 is complete when the evidence cycle closes, not when the repository accumulates features."),
        bullet("All deterministic, pairing, shock-magnitude, censoring, and checkpoint tests pass."),
        bullet("The independent pilot is executed once and N is recorded transparently."),
        bullet("Confirmatory seeds are selected mechanically from the frozen pool."),
        bullet("No tuning or adaptive intervention occurs during confirmatory execution."),
        bullet("The automatic report includes passed and failed gates, uncertainty, limitations, and failures."),
        bullet("The decision is documented even when the hypothesis is unsupported or inconclusive."),
        Spacer(1, 10),
        P("The project remains faithful to its origin by treating local adaptation as a mechanism to test, not a metaphor to protect. Its capacity to grow comes from stable contracts and evidence gates, not from adding every future feature to the first implementation."),
        Spacer(1, 18),
        Table([[P("NEXT ACTION", "callout")], [P("Review the frozen artifacts, run the development POC locally, then execute the independent pilot. Do not unlock the confirmatory configuration before the sample-size addendum is committed.")]], colWidths=[6.5 * inch], style=TableStyle([("BACKGROUND", (0, 0), (-1, 0), MINT), ("BOX", (0, 0), (-1, -1), 0.8, GREEN), ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 11), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12)])),
    ]
    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = MGDocument(str(OUTPUT))
    document.build(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    main()

