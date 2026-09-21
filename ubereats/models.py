from dataclasses import dataclass


@dataclass(frozen=True)
class Store:
    uuid: str
    title: str
    url: str | None = None
    rating: str | None = None
    eta: str | None = None
    image: str | None = None


@dataclass(frozen=True)
class Item:
    uuid: str
    title: str
    price: int
    description: str | None = None
    sold_out: bool = False
    customizable: bool = False
    section_uuid: str | None = None


@dataclass(frozen=True)
class MenuSection:
    title: str
    items: tuple[Item, ...]


@dataclass(frozen=True)
class Menu:
    store_uuid: str
    title: str
    currency: str
    eta: str | None
    sections: tuple[MenuSection, ...]

    @property
    def item_count(self) -> int:
        return sum(len(section.items) for section in self.sections)


@dataclass(frozen=True)
class Address:
    label: str
    latitude: float
    longitude: float
    formatted: str


def format_price(minor_units: int, currency: str) -> str:
    return f"{minor_units / 100:.2f} {currency}"
