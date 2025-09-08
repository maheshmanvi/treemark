# tree_mark/cli/app.py
"""
Interactive CLI for TreeMark.

MODIFICATIONS:
- Accept 'exit' at any prompt to terminate immediately.
- Accept 'back' at prompts to step back one level in interactive flow.
- Default vs Custom selections behavior implemented.
- Integrates with new JSON format (tree + flat).
- Keeps previous simple generate command behavior intact.
"""

import os
import sys
import asyncio
import typer
from typing import Optional, List

from loguru import logger

from tree_mark.core.models.schemas import OutputFormat
from tree_mark.core.usecases.generate_structure import GenerateStructureUseCase
from tree_mark.core.models.usecase_result import UseCaseResult
from tree_mark.logging_config import configure_logging
from tree_mark.cli.progress import console

from tree_mark.utils.io_helpers import ensure_outputs_dir, sanitize_path_for_filename
from tree_mark.adapters.serializers.json_serializer import (
    deserialize_json_to_tree,
    serialize_to_json,
    node_to_tree_dict,
    flatten_tree_to_paths,
)
from tree_mark.adapters.serializers.markdown_serializer import (
    parse_markdown_to_tree,
    serialize_to_markdown,
)
from tree_mark.adapters.repository.file_repository import write_text_file, write_json_file
from tree_mark.scripts.create_from_json import recreate_from_json

app = typer.Typer(help="TreeMark CLI — generate folder structure as JSON/Markdown and recreate from JSON")


# -------------------------
# Small interactive helpers
# -------------------------
class BackSignal(Exception):
    """Raised when user types 'back' to go to previous menu."""
    pass

def check_exit_back(raw: Optional[str]) -> Optional[str]:
    """
    Check a raw input string: if 'exit' -> terminate application.
    if 'back' -> raise BackSignal.
    otherwise return the original string.
    """
    if raw is None:
        return raw
    s = raw.strip()
    if s.lower() == "exit":
        console.print("[bold red]Exit command received. Terminating...[/bold red]")
        sys.exit(0)
    if s.lower() == "back":
        raise BackSignal()
    return raw

def prompt_with_controls(prompt_text: str, default: Optional[str] = None) -> str:
    """
    Wrapper around typer.prompt that supports 'exit' and 'back'.
    Returns the user input string (not stripped).
    Raises BackSignal if 'back' pressed.
    Exits if 'exit' pressed.
    """
    raw = typer.prompt(prompt_text, default=default)
    return check_exit_back(raw)


# -------------------------
# CLI Commands
# -------------------------
@app.command()
def generate(
    folder: str = typer.Argument(..., help="Path of the folder or archive to scan"),
    output: OutputFormat = typer.Option(OutputFormat.BOTH, help="Output format: json, markdown or both"),
    include_extensions: Optional[str] = typer.Option(None, help="Comma-separated extensions to include (e.g. .py,.md)"),
    exclude_extensions: Optional[str] = typer.Option(None, help="Comma-separated extensions to exclude (e.g. .log,.tmp)"),
    scanner_kind: str = typer.Option('auto', help="Scanner kind: auto|local|zip"),
    concurrency: int = typer.Option(10, help="Maximum concurrency for scanning (recommended 5-50 depending on system)"),
    outputs_dir: str = typer.Option('outputs', help="Directory to store generated outputs"),
    keep_extensions: bool = typer.Option(True, help="Keep file extensions in generated outputs (Y/n)"),
    interactive: bool = typer.Option(False, help="If true, enter interactive mode"),
):
    """
    Non-interactive generate command (keeps prior behaviour).
    Use --interactive to run the menu-driven loop.
    """
    configure_logging()
    logger.info("CLI -> generate called folder={}", folder)

    include_exts: Optional[List[str]] = None
    exclude_exts: Optional[List[str]] = None

    if interactive:
        # If interactive flag is passed to generate, hand off to the interactive flow
        console.print("Interactive flag detected — launching interactive mode...")
        asyncio.run(_interactive_main(default_outputs_dir=outputs_dir))
        return

    if include_extensions:
        include_exts = [e.strip() for e in include_extensions.split(',') if e.strip()]
    if exclude_extensions:
        exclude_exts = [e.strip() for e in exclude_extensions.split(',') if e.strip()]

    usecase = GenerateStructureUseCase(scanner_kind=scanner_kind, max_concurrency=concurrency)

    async def _run():
        with console.status(f"Scanning {folder}..."):
            res = await usecase.generate(folder, include_exts, exclude_exts, output, outputs_dir, keep_extensions)

        # Normalize return shapes
        if isinstance(res, UseCaseResult):
            results, elapsed = res.results, res.elapsed
        elif isinstance(res, tuple) and len(res) == 2:
            results, elapsed = res
        elif isinstance(res, dict):
            results, elapsed = res, 0.0
        else:
            results, elapsed = {}, 0.0

        console.print("\n[green]Done.[/green]")
        if results:
            for k, v in results.items():
                console.print(f"  - {k.upper()}: {v}")
        else:
            console.print("  - (no output files produced)")
        console.print(f"  - Time taken: {elapsed:.3f}s\n")

    asyncio.run(_run())


# -------------------------
# Interactive entrypoint
# -------------------------
@app.command(name="interactive")
def interactive(default_outputs_dir: str = typer.Option('outputs', help="Default outputs directory used by interactive session")):
    """
    Start interactive menu.
    """
    configure_logging()
    try:
        asyncio.run(_interactive_main(default_outputs_dir=default_outputs_dir))
    except KeyboardInterrupt:
        console.print("\n[bold red]Interactive session terminated by user.[/bold red]")


async def _interactive_main(default_outputs_dir: str = 'outputs'):
    """
    The core interactive loop implemented as an async function to allow awaiting usecase methods directly.
    This function implements:
      - default vs custom flows
      - 'exit' anywhere to quit
      - 'back' to step back in a nested flow
    """
    console.rule("[bold green]TreeMark — Interactive Mode[/]")
    console.print("Type the number of an option, or the option text (e.g. 1 or 'scan').")
    console.print("Type 'exit' anytime to quit, or 'back' to go to the previous step.\n")

    # navigation stack not strictly necessary here; we use BackSignal to return to previous prompt
    while True:
        main_menu = (
            "\nMain menu — choose an action:\n"
            "  1) Scan folder -> generate JSON/Markdown/Both\n"
            "  2) Recreate filesystem from JSON or Markdown\n"
            "  3) Convert JSON -> Markdown\n"
            "  4) Convert Markdown -> JSON\n"
            "  5) Exit\n"
        )
        console.print(main_menu)
        try:
            raw_choice = prompt_with_controls("Enter option (number or text)", default="1").strip().lower()
        except BackSignal:
            # no previous (at top) -> ignore
            continue

        choice = raw_choice

        # 1 -> Scan flow
        if choice in ("1", "scan", "scan folder", "scan folder -> generate json/markdown/both"):
            try:
                folder = prompt_with_controls("Enter folder or archive path to scan (absolute or relative)")
                # ask default vs custom
                try:
                    proceed_default = typer.confirm(
                        "Proceed with Default settings? (Outputs: both | Keep extensions: Yes | Outputs dir: outputs | Concurrency: 10)",
                        default=True
                    )
                except BackSignal:
                    # user chose back at confirmation -> go back to folder entry
                    continue

                if proceed_default:
                    out_fmt = OutputFormat.BOTH
                    keep_ext = True
                    outputs_dir = default_outputs_dir
                    concurrency = 10
                else:
                    # custom flow; each prompt supports back/exit
                    try:
                        fmt_choice = prompt_with_controls("Output format — enter 1 JSON, 2 Markdown, 3 Both (press Enter for default=3)", default="3")
                        fmt_choice = fmt_choice.strip()
                    except BackSignal:
                        # go back to folder input
                        continue
                    out_fmt = OutputFormat.JSON if fmt_choice == "1" or fmt_choice.lower().startswith("j") else (OutputFormat.MARKDOWN if fmt_choice == "2" or fmt_choice.lower().startswith("m") else OutputFormat.BOTH)

                    try:
                        ke = prompt_with_controls("Keep file extensions in outputs? (Y/n) — default: Y", default="Y")
                    except BackSignal:
                        continue
                    keep_ext = False if ke.lower().startswith("n") else True

                    try:
                        outputs_dir = prompt_with_controls("Outputs directory (press Enter for default 'outputs')", default=default_outputs_dir)
                    except BackSignal:
                        continue

                    try:
                        concurrency_input = prompt_with_controls("Concurrency (parallel workers) — how many files to scan at once? (press Enter for default 10)", default="10")
                    except BackSignal:
                        continue
                    try:
                        concurrency = int(concurrency_input)
                    except Exception:
                        concurrency = 10

                # run the usecase
                usecase = GenerateStructureUseCase(scanner_kind='auto', max_concurrency=concurrency)
                console.print(f"\n[blue]Scanning:[/blue] {folder}")
                console.print(f"[blue]Output format:[/blue] {out_fmt}   [blue]Keep extensions:[/blue] {'Yes' if keep_ext else 'No'}   [blue]Outputs dir:[/blue] {outputs_dir}\n")

                # call usecase and normalize result
                with console.status(f"Scanning {folder}..."):
                    res = await usecase.generate(folder, None, None, out_fmt, outputs_dir, keep_ext)

                if isinstance(res, UseCaseResult):
                    results, elapsed = res.results, res.elapsed
                elif isinstance(res, tuple) and len(res) == 2:
                    results, elapsed = res
                elif isinstance(res, dict):
                    results, elapsed = res, 0.0
                else:
                    results, elapsed = {}, 0.0

                console.print("\n[green]Scan complete.[/green]")
                if results:
                    # If results contains a 'json' path, attempt to pretty-print brief summary:
                    if "json" in results:
                        console.print(f"  - JSON: {results['json']}")
                        # Optionally show the 'flat' preview from the generated JSON (if present)
                        try:
                            # load generated json to show top 3 flat entries for convenience
                            import json as _json
                            with open(results['json'], 'r', encoding='utf8') as jf:
                                jdata = _json.load(jf)
                                flat = jdata.get('flat') if isinstance(jdata, dict) else None
                                if flat and isinstance(flat, list):
                                    console.print("  - sample files:")
                                    for p in flat[:3]:
                                        console.print(f"      * {p}")
                        except Exception:
                            pass
                    else:
                        for k, v in results.items():
                            console.print(f"  - {k.upper()}: {v}")
                else:
                    console.print("  - (no output files produced)")

                console.print(f"  - Time taken: {elapsed:.3f}s\n")

            except BackSignal:
                # go back to main menu
                continue

        # 2 -> Recreate from JSON/MD
        elif choice in ("2", "recreate", "recreate filesystem", "create from json"):
            try:
                src_file = prompt_with_controls("Enter path to JSON or Markdown file to recreate from")
                dest_dir = prompt_with_controls("Enter destination folder to create the structure")
                dry_run_input = prompt_with_controls("Dry run? (Yes = show actions only) (Y/n)", default="Y")
                dry_run = False if dry_run_input.lower().startswith("n") else True
            except BackSignal:
                continue

            suffix = os.path.splitext(src_file)[1].lower()
            if suffix == ".json":
                console.print(f"[blue]Recreating from JSON:[/blue] {src_file} -> {dest_dir} (dry_run={dry_run})")
                await recreate_from_json(src_file, dest_dir, dry_run)
                console.print("[green]Done.[/green]\n")
            elif suffix in (".md", ".markdown", ""):
                console.print("[blue]Converting Markdown -> JSON then recreating...[/blue]")
                md_text = open(src_file, 'r', encoding='utf8').read()
                tree = parse_markdown_to_tree(md_text)
                json_obj = await serialize_to_json(tree)
                outputs_dir = ensure_outputs_dir(default_outputs_dir)
                fname = os.path.join(outputs_dir, sanitize_path_for_filename(src_file) + ".json")
                await write_json_file(fname, json_obj)
                await recreate_from_json(fname, dest_dir, dry_run)
                console.print("[green]Done.[/green]\n")
            else:
                console.print("[red]Unsupported file type. Please provide a .json or .md file.[/red]\n")

        # 3 -> JSON -> Markdown
        elif choice in ("3", "convert json", "json->md", "json to markdown"):
            try:
                src_json = prompt_with_controls("Enter path to JSON file to convert to Markdown")
                outputs_dir = prompt_with_controls("Outputs directory (press Enter for default 'outputs')", default=default_outputs_dir)
            except BackSignal:
                continue

            try:
                with open(src_json, 'r', encoding='utf8') as f:
                    import json as _json
                    jdata = _json.load(f)
                # handle combined format or legacy
                tree_root = deserialize_json_to_tree(jdata)
                ke = prompt_with_controls("Keep file extensions in Markdown? (Y/n) — default: Y", default="Y")
                keep_ext = False if ke.lower().startswith("n") else True
                md_text = await serialize_to_markdown(tree_root, keep_extensions=keep_ext)
                outputs_dir = ensure_outputs_dir(outputs_dir)
                fname = os.path.join(outputs_dir, sanitize_path_for_filename(src_json) + ".md")
                await write_text_file(fname, md_text)
                console.print(f"[green]Wrote Markdown to {fname}[/green]\n")
            except BackSignal:
                continue
            except Exception as exc:
                console.print(f"[red]Failed to convert JSON to Markdown: {exc}[/red]")

        # 4 -> Markdown -> JSON
        elif choice in ("4", "convert md", "md->json", "markdown to json"):
            try:
                src_md = prompt_with_controls("Enter path to Markdown file to convert to JSON")
                outputs_dir = prompt_with_controls("Outputs directory (press Enter for default 'outputs')", default=default_outputs_dir)
            except BackSignal:
                continue

            try:
                md_text = open(src_md, 'r', encoding='utf8').read()
                tree = parse_markdown_to_tree(md_text)
                ke = prompt_with_controls("Keep file extensions in JSON 'name' fields? (Y/n) — default: Y", default="Y")
                keep_ext = False if ke.lower().startswith("n") else True
                json_obj = await serialize_to_json(tree, keep_extensions=keep_ext)
                outputs_dir = ensure_outputs_dir(outputs_dir)
                fname = os.path.join(outputs_dir, sanitize_path_for_filename(src_md) + ".json")
                await write_json_file(fname, json_obj)
                console.print(f"[green]Wrote JSON to {fname}[/green]\n")
            except BackSignal:
                continue
            except Exception as exc:
                console.print(f"[red]Failed to convert Markdown to JSON: {exc}[/red]")

        elif choice in ("5", "exit", "quit", "q"):
            console.print("[bold red]Exiting interactive mode. Goodbye![/bold red]")
            break

        else:
            console.print("[yellow]Unknown option. Please type the number (e.g. 1) or the option text (e.g. 'scan').[/yellow]")


# -------------------------
# End of file
# -------------------------
