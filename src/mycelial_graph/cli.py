"""Command-line entry point for Mycelial Graph V0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import yaml

from .config import load_config
from .experiment import run_experiment
from .graph import HardPolicy, LayeredGraph
from .report import write_report
from .trial import FrozenTrial


def _seeds(value: str | None) -> Iterable[int] | None:
    if value is None:
        return None
    parsed = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise argparse.ArgumentTypeError("--seeds needs at least one integer")
    return parsed


def _snapshot_config(config: dict, output: Path) -> None:
    with (output / "frozen_config.yaml").open("w", encoding="utf-8") as stream:
        yaml.safe_dump(config, stream, sort_keys=False)


def _run(args: argparse.Namespace, *, demo: bool) -> int:
    frozen = load_config(args.config)
    config = frozen.copy()
    output = Path(args.output).resolve()
    selected = _seeds(args.seeds)
    if demo and selected is None:
        selected = (int(config["experiment"]["seeds"][0]),)
    results = run_experiment(
        config,
        output,
        seeds=selected,
        save_trials=not args.no_save_trials,
    )
    _snapshot_config(config, output)
    report = write_report(results, output / "REPORT.md")
    print(f"Mycelial Graph {config['project']['version']} completed.")
    print(f"Results: {output / 'results.json'}")
    print(f"Report:  {report}")
    print("Scientific status: demonstrator only; H1/H2/H3 remain untested.")
    return 0


def _freeze(args: argparse.Namespace) -> int:
    frozen = load_config(args.config)
    config = frozen.copy()
    graph = LayeredGraph.from_config(config["graph"])
    HardPolicy.from_config(config["policy"])
    trial = FrozenTrial.generate(graph, config, int(args.seed))
    target = trial.save(Path(args.output).resolve())
    print(json.dumps({"path": str(target), "seed": trial.seed, "sha256": trial.digest}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mycelial-graph",
        description="Run the Mycelial Graph V0 synthetic demonstrator.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("demo", "run one seed and generate a compact report"),
        ("experiment", "run the configured multi-seed V0 comparison"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--config", default="configs/v0_demo.yaml")
        command.add_argument(
            "--output",
            default="outputs/demo" if name == "demo" else "outputs/v0_results",
        )
        command.add_argument("--seeds", help="comma-separated override, for example 101,211")
        command.add_argument("--no-save-trials", action="store_true")
        command.set_defaults(handler=lambda args, demo=(name == "demo"): _run(args, demo=demo))

    freeze = subparsers.add_parser("freeze", help="pre-generate one immutable trial")
    freeze.add_argument("--config", default="configs/v0_demo.yaml")
    freeze.add_argument("--seed", type=int, default=101)
    freeze.add_argument("--output", default="outputs/trial_seed_101.json.gz")
    freeze.set_defaults(handler=_freeze)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.handler(args))

