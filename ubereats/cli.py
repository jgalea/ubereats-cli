import typer

from . import __version__

app = typer.Typer(add_completion=False, help="Unofficial CLI for Uber Eats.")


@app.callback()
def cli() -> None:
    pass


@app.command()
def version() -> None:
    typer.echo(__version__)


def main() -> None:
    app()
