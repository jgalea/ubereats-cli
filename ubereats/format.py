import dataclasses
import itertools
import json

from rich.console import Console
from rich.table import Table

from .models import Menu, format_price


def to_jsonable(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def _cell(value) -> str:
    if value is None:
        return ""
    text = str(value)
    if any(ch in text for ch in (",", '"', "\n")):
        return '"' + text.replace('"', '""') + '"'
    return text


def to_toon(value, *, root: str = "data") -> str:
    value = to_jsonable(value)
    if isinstance(value, list):
        if not value:
            return f"{root}[0]{{}}:"
        if all(isinstance(row, dict) for row in value):
            fields = list(value[0].keys())
            if all(list(row.keys()) == fields for row in value):
                head = f"{root}[{len(value)}]{{{','.join(fields)}}}:"
                rows = ["  " + ",".join(_cell(row[f]) for f in fields) for row in value]
                return "\n".join([head] + rows)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {_cell(v)}" for k, v in value.items())
    return f"{root}: {_cell(value)}"


def render_stores(stores, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(to_jsonable(stores), ensure_ascii=False, indent=2))
        return
    if fmt == "toon":
        rows = [
            {"uuid": s.uuid, "title": s.title, "eta": s.eta, "rating": s.rating} for s in stores
        ]
        print(to_toon(rows, root="stores"))
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Store")
    table.add_column("ETA")
    table.add_column("Rating")
    for number, store in enumerate(stores, start=1):
        table.add_row(str(number), store.title, store.eta or "", store.rating or "")
    Console().print(table)


def render_menu(menu: Menu, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(to_jsonable(menu), ensure_ascii=False, indent=2))
        return
    if fmt == "toon":
        rows = [
            {
                "section": section.title,
                "uuid": item.uuid,
                "title": item.title,
                "price": item.price,
                "sold_out": item.sold_out,
                "customizable": item.customizable,
            }
            for section in menu.sections
            for item in section.items
        ]
        print(to_toon(rows, root="items"))
        return
    console = Console()
    counter = itertools.count(1)
    header = f"{menu.title}  ({menu.item_count} items"
    header += f", {menu.eta})" if menu.eta else ")"
    console.print(header, style="bold")
    for section in menu.sections:
        table = Table(
            title=section.title, title_justify="left", show_header=True, header_style="bold"
        )
        table.add_column("#", justify="right", style="dim")
        table.add_column("Item")
        table.add_column("Price", justify="right")
        for item in section.items:
            name = item.title + (" (sold out)" if item.sold_out else "")
            table.add_row(str(next(counter)), name, format_price(item.price, menu.currency))
        console.print(table)
