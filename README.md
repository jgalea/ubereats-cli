<h1 align="center">ubereats-cli</h1>

<p align="center">
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/PYTHON-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/LICENSE-MIT-5C9E31?style=for-the-badge" alt="License"></a>
  <a href="https://rebelcode.com"><img src="https://img.shields.io/badge/BUILT%20BY-REBELCODE-8A2BE2?style=for-the-badge" alt="Built by RebelCode"></a>
</p>

<p align="center"><strong>Unofficial CLI for Uber Eats. Set a delivery address, find restaurants, and read menus from the terminal.</strong></p>

---

## Overview

`ubereats` talks to the same `www.ubereats.com/_p/api` endpoints the website calls. It isn't a scraper of rendered pages.

Uber puts Cloudflare in front of those endpoints, and a plain HTTP client gets a `403` challenge on every request. This CLI uses [curl_cffi](https://github.com/lexiforest/curl_cffi) to match Chrome's TLS fingerprint, which is what gets through. No headless browser, no account needed for anything in this release.

Every command supports `--json` (data to stdout, logs to stderr) and `--toon` (fewer tokens, for agents).

## Commands

```
ubereats <command> [flags]

  address                   show the saved delivery address
  address <query>           geocode an address and save it
  search <query...>         find stores delivering to that address
  menu <store>              list a store's sections and items
  version

FLAGS
  --pick N                  which geocoding match to keep (address)
  --limit N                 how many results (search, default 20)
  --exclude "a,b"           hide stores by name, or 'none' to disable
  --locale                  locale code, default pt
  --json                    raw JSON to stdout, logs to stderr
  --toon                    TOON output, fewer tokens for agents

ENV
  UBEREATS_CONFIG_DIR       override ~/.ubereats
  UBEREATS_DEBUG=1          dump requests and responses to stderr
```

## Address

Every lookup needs to know where you're ordering to. Uber keeps that in a `uev2.loc` cookie, and this CLI builds it from coordinates:

```bash
ubereats address "Avenida Marginal, Cascais, Portugal"
```

The query is geocoded through [Nominatim](https://nominatim.openstreetmap.org). When several places match, all of them are listed on stderr and the first is kept; `--pick 3` takes another. The choice is cached in `~/.ubereats/location.json`, so you set it once.

## Searching and menus

```bash
ubereats search sushi --limit 5
ubereats search poke --json | jq '.[].title'
ubereats menu 49d6a3e6-7795-41db-b5ec-8c1f6d9156b1 --toon
```

`menu` takes a store uuid or a store URL, so you can paste a link straight from the browser:

```bash
ubereats menu https://www.ubereats.com/pt/store/sushi-yatomi/Sdaj5neVQdu17IwfbZFWsQ
```

`search --exclude "domino,pizza hut"` hides stores by name, for the places you never want to see. Keep a standing list in `~/.ubereats/exclude.txt`, one name per line, and pass `--exclude none` for a search that shows everything. Whatever is hidden is reported on stderr, so a short result list is never quietly a filtered one.

## Install

```bash
git clone https://github.com/jgalea/ubereats-cli.git
cd ubereats-cli
uv tool install .
ubereats version
```

## Status

Browsing works end to end: address, search, menus. Logging in, filling a cart, and placing an order are not in this release. Those endpoints need traffic captured from a real checkout before they can be written honestly, and guessing at them is how you ship a broken order button.

## When it stops answering

Uber runs its own reCAPTCHA bot defense in front of these endpoints, separate from Cloudflare. A burst of requests from one address trips it, and the API starts returning `403` with `metadata.botdefense.state: challenge` while the website itself still loads normally. The CLI tells you which of the two you hit, because the fix differs: a Cloudflare interstitial means the TLS fingerprint stopped matching, while a bot-defense challenge means you've been noisy. Retrying doesn't clear the latter. Open ubereats.com in a browser on the same connection, complete the check, and give it a few minutes.

Keep the request rate sane and you won't see it.

## Exit codes

| code | meaning |
|---|---|
| 4 | blocked by Cloudflare or Uber's bot defense |
| 5 | no session, or it expired |
| 6 | no delivery address set |
| 7 | store or item not found |
| 8 | Uber returned an error |

## License

MIT. See [LICENSE](LICENSE).

Author: Jean Galea. Unofficial project, not affiliated with or endorsed by Uber. It talks to the same endpoints ubereats.com uses in your browser, so use it at a sane request rate.
