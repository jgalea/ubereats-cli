import sys

import typer

from . import __version__
from . import exclude as exclude_mod
from . import location
from . import recent
from .errors import UberEatsError
from .format import render_menu, render_stores
from .search import search as do_search
from .session import Session
from .store import menu as do_menu

app = typer.Typer(add_completion=False, help="Unofficial CLI for Uber Eats.")


@app.callback()
def cli() -> None:
    pass


def build_session(locale: str = "pt"):
    session = Session(locale=locale)
    session.load()
    location.apply_to(session, location.load_address())
    return session


def _fmt(as_json: bool, as_toon: bool) -> str:
    if as_json:
        return "json"
    if as_toon:
        return "toon"
    return "table"


def _run(fn):
    try:
        return fn()
    except UberEatsError as err:
        typer.echo(str(err))
        raise typer.Exit(code=err.exit_code)


@app.command()
def version() -> None:
    typer.echo(__version__)


@app.command()
def address(
    query: str = typer.Argument(None, help="Address to geocode and save"),
    pick: int = typer.Option(1, "--pick", help="Which match to keep, 1-based"),
) -> None:
    if query is None:
        current = _run(location.load_address)
        typer.echo(f"{current.formatted}  ({current.latitude}, {current.longitude})")
        return
    matches = _run(lambda: location.geocode(query))
    if len(matches) > 1 and pick == 1:
        for index, match in enumerate(matches, start=1):
            print(f"  {index}. {match.formatted}", file=sys.stderr)
        print("Keeping 1. Use --pick N to choose another.", file=sys.stderr)
    chosen = matches[min(max(pick, 1), len(matches)) - 1]
    location.save_address(chosen)
    typer.echo(f"{chosen.formatted}  ({chosen.latitude}, {chosen.longitude})")


@app.command()
def search(
    query: list[str] = typer.Argument(..., help="What to look for"),
    limit: int = typer.Option(20, "--limit"),
    exclude: str = typer.Option(None, "--exclude", help="Comma-separated names to hide, or 'none'"),
    locale: str = typer.Option("pt", "--locale"),
    as_json: bool = typer.Option(False, "--json"),
    as_toon: bool = typer.Option(False, "--toon"),
) -> None:
    text = " ".join(query)
    session = _run(lambda: build_session(locale))
    stores = _run(lambda: do_search(session, text, limit=limit))
    kept, hidden = exclude_mod.apply(stores, exclude_mod.load_exclusions(exclude))
    recent.save("stores", [store.uuid for store in kept])
    if hidden:
        names = ", ".join(store.title for store in hidden)
        print(f"{len(hidden)} hidden by --exclude: {names}", file=sys.stderr)
    render_stores(kept, _fmt(as_json, as_toon))


@app.command()
def menu(
    store: str = typer.Argument(..., help="Row number from the last search, a store uuid, or a store URL"),
    locale: str = typer.Option("pt", "--locale"),
    as_json: bool = typer.Option(False, "--json"),
    as_toon: bool = typer.Option(False, "--toon"),
) -> None:
    if store.isdigit():
        from_recent = recent.lookup("stores", int(store))
        if from_recent is None:
            typer.echo(f"No store {store} in the last search. Run a search first.")
            raise typer.Exit(code=7)
        store = from_recent
    session = _run(lambda: build_session(locale))
    result = _run(lambda: do_menu(session, store))
    render_menu(result, _fmt(as_json, as_toon))


def main() -> None:
    # A Windows console or pipe may not be UTF-8; print what it can rather than crash.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    app()
