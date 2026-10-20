#!/usr/bin/env python3

import sys
from pathlib import Path

import requests

API_URL = "https://api.mcstatus.io/v2/status/java/cookie-smp.minecraft.party"
TEAM_ACCOUNTS = {
    "Kecks_Kruemmel": "Owner",
    "Jecrafter": "Manager",
    "Drr_Benjii": "Admin",
    "Tobias86825": "Developer",
    "Staffcrafter": "Moderator",
    "DDR_Maik": "Moderator",
}


def normalize_name(value: str) -> str:
    return value.strip().casefold()


def fetch_online_players() -> set[str] | None:
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("online"), bool):
            raise ValueError("Unerwartetes Format der Serverstatus-Antwort.")
    except (requests.RequestException, ValueError) as exc:
        print(f"[WARN] Konnte Serverstatus nicht abrufen: {exc}", file=sys.stderr)
        return None

    if not data["online"]:
        return set()

    players = data.get("players")
    player_list = players.get("list") if isinstance(players, dict) else None
    online_count = players.get("online") if isinstance(players, dict) else None
    if not isinstance(player_list, list) or not isinstance(online_count, int):
        print("[WARN] Server online, aber keine Spielerstatus-Liste verfügbar.", file=sys.stderr)
        return None

    team_names = {normalize_name(account) for account in TEAM_ACCOUNTS}
    names = set()
    for player in player_list:
        if not isinstance(player, dict):
            continue
        name = player.get("name_clean")
        if isinstance(name, str) and normalize_name(name) in team_names:
            names.add(normalize_name(name))

    if online_count > 0 and len(player_list) != online_count:
        print(
            "[WARN] Server online, aber die API liefert keine vollständige "
            "Spielerliste; Teamstatus ist unbekannt.",
            file=sys.stderr,
        )
        return None

    return names


def update_team_status_table(
    readme_text: str, online_players: set[str] | None
) -> str:
    lines = readme_text.splitlines()

    section_start = None
    for idx, line in enumerate(lines):
        if line.strip() == "## 👥 Team Übersicht":
            section_start = idx
            break

    if section_start is None:
        raise RuntimeError("Abschnitt '## 👥 Team Übersicht' nicht gefunden.")

    table_start = section_start + 1
    while table_start < len(lines) and lines[table_start].strip() == "":
        table_start += 1

    while table_start < len(lines) and not lines[table_start].strip().startswith("|"):
        table_start += 1

    if table_start >= len(lines):
        raise RuntimeError("Team-Übersichtstabelle nicht gefunden.")

    table_end = table_start
    while table_end < len(lines) and lines[table_end].strip().startswith("|"):
        table_end += 1

    table_lines = lines[table_start:table_end]
    if not table_lines or not table_lines[0].strip().startswith("| Rolle |"):
        raise RuntimeError("Team-Übersichtstabelle hat ein falsches Format.")

    online_team_members = (
        {normalize_name(name) for name in online_players}
        if online_players is not None
        else set()
    )

    updated_table = [table_lines[0], table_lines[1]]
    for row in table_lines[2:]:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue

        role = cells[0]
        name = cells[1]
        if online_players is None:
            status = "⚪ Unbekannt"
        else:
            status = (
                "🟢 Online"
                if normalize_name(name) in online_team_members
                else "🔴 Offline"
            )
        updated_table.append(f"| {role} | {name} | {status} |")

    new_lines = lines[:table_start] + updated_table + lines[table_end:]
    return "\n".join(new_lines).rstrip() + "\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    readme_path = repo_root / "README.md"

    online_players = fetch_online_players()
    readme_text = readme_path.read_text(encoding="utf-8")
    updated_readme = update_team_status_table(readme_text, online_players)
    readme_path.write_text(updated_readme, encoding="utf-8")

    count = len(online_players) if online_players is not None else "unbekannt"
    print(f"[INFO] Team-Status aktualisiert. Erkannte Teammitglieder online: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
