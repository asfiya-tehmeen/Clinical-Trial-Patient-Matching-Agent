"""
cli.py
======
Command-line interface for the Clinical Trial Patient Matching Agent.

    ctmatch init                         save your Groq API key
    ctmatch check                        verify key + connectivity
    ctmatch samples                      list built-in sample patients
    ctmatch match --sample A_nsclc       run on a sample patient
    ctmatch match --file note.txt        run on your own EHR note
    ctmatch match -                      read the note from stdin
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

ENV_FILE = Path.home() / ".ctmatch.env"


def _cmd_init(args):
    key = args.key or getpass.getpass("Paste your Groq API key (gsk_...): ").strip()
    if not key:
        print("No key entered.", file=sys.stderr)
        return 1
    ENV_FILE.write_text(f"GROQ_API_KEY={key}\n", encoding="utf-8")
    try:
        ENV_FILE.chmod(0o600)
    except OSError:
        pass
    print(f"✅ Saved to {ENV_FILE}. Run `ctmatch check` to verify.")
    return 0


def _cmd_check(args):
    from .config import call_llm, MODEL_FAST
    print(f"Testing Groq connection with {MODEL_FAST}...")
    reply = call_llm("Reply with the single word: ok", MODEL_FAST, max_tokens=5)
    print(f"✅ Groq responded: {reply!r}")
    return 0


def _cmd_samples(args):
    from .patients import SAMPLE_PATIENTS
    for name, text in SAMPLE_PATIENTS.items():
        first = " ".join(text.split())[:90]
        print(f"  {name:<14} {first}...")
    return 0


def _read_note(args) -> str:
    from .patients import SAMPLE_PATIENTS
    if args.sample:
        if args.sample not in SAMPLE_PATIENTS:
            raise SystemExit(f"Unknown sample '{args.sample}'. Options: {', '.join(SAMPLE_PATIENTS)}")
        return SAMPLE_PATIENTS[args.sample]
    if args.note == "-":
        return sys.stdin.read()
    if args.note or args.file:
        path = Path(args.file or args.note)
        if not path.is_file():
            raise SystemExit(f"File not found: {path}")
        return path.read_text(encoding="utf-8")
    raise SystemExit("Provide a note: --sample NAME, --file PATH, or '-' for stdin.")


def _cmd_match(args):
    note = _read_note(args)
    if not note.strip():
        raise SystemExit("The clinical note is empty.")
    from .pipeline import run_pipeline
    run_pipeline(note, max_trials=args.max_trials, top_k=args.top_k,
                 output_path=args.output, show_table=not args.no_table)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ctmatch", description="Clinical trial patient matching agent")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="save your Groq API key to ~/.ctmatch.env")
    s.add_argument("--key", help="key to save (omit to be prompted)")
    s.set_defaults(func=_cmd_init)

    s = sub.add_parser("check", help="verify the API key works")
    s.set_defaults(func=_cmd_check)

    s = sub.add_parser("samples", help="list built-in sample patients")
    s.set_defaults(func=_cmd_samples)

    s = sub.add_parser("match", help="match a patient note to recruiting trials")
    s.add_argument("note", nargs="?", help="path to a note file, or '-' for stdin")
    s.add_argument("--file", "-f", help="path to a plain-text EHR note")
    s.add_argument("--sample", "-s", help="use a built-in sample patient (see `ctmatch samples`)")
    s.add_argument("--max-trials", type=int, default=25, help="trials to fetch (default 25)")
    s.add_argument("--top-k", type=int, default=5, help="matches to display (default 5)")
    s.add_argument("--output", "-o", default="trial_matching_results.json",
                   help="JSON results path (default trial_matching_results.json)")
    s.add_argument("--no-table", action="store_true", help="skip the full results table")
    s.set_defaults(func=_cmd_match)
    return p


def main(argv=None) -> int:
    # Output uses emoji/box characters; avoid crashes on legacy Windows consoles.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        from .config import MissingAPIKeyError
        if isinstance(e, MissingAPIKeyError):
            print(f"❌ {e}", file=sys.stderr)
            return 2
        if os.getenv("CTMATCH_DEBUG"):
            raise
        print(f"❌ {type(e).__name__}: {e}  (set CTMATCH_DEBUG=1 for a traceback)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
