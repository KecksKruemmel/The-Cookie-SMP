#!/usr/bin/env python3

import socket
import sys
from pathlib import Path

import requests

API_URL = "https://api.mcsrvstat.us/3/cookie-smp.minecraft.party"
HOST = "cookie-smp.minecraft.party"
PORTS = (25565, 6554)
TEAM_ACCOUNTS = {
    "Kecks_Krümmel": "Owner",
    "Jecrafter": "Manager",
    "Drr_Benjii": "Admin",
    "Tobias86825": "Developer",
    "Staffcrafter": "Moderator",
    "DDR_Maik": "Moderator",
}


def normalize_name(value: str) -> str:
    return value.strip().casefold()


def is_server_reachable() -> bool:
    for port in PORTS:
        try:
            infos = socket.getaddrinfo(HOST, port, type=socket.SOCK_STREAM)
        except socket.gaierror:
            continue

        for family, socktype, proto, _, sockaddr in infos:
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                sock.settimeout(5)
                sock.connect(sockaddr)
                return True
            except OSError:
                continue
            finally:
                if sock is not None:
                    sock.close()
    return False


def extract_player_names(payload: object) -> set[str]:
    players = payload.get("players") if isinstance(payload, dict) else None
    if isinstance(players, dict):
        player_entries = players.get("list") or []
    elif isinstance(players, list):
        player_entries = players
    else:
        player_entries = []

    names: list[str] = []
    for player in player_entries:
        if isinstance(player, dict):
            name = player.get("name")
        else:
            name = player
        if isinstance(name, str) and name.strip():
            names.append(name)
    return {normalize_name(name) for name in names}


def fetch_online_players() -> set[str]:
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        players = extract_player_names(data)
        if players:
            return players
    except Exception as exc:
        print(f"[WARN] Konnte Serverstatus nicht abrufen: {exc}", file=sys.stderr)

    if is_server_reachable():
        print("[INFO] Server erreichbar, verwende Fallback für Teamstatus.", file=sys.stderr)
        return {normalize_name(name) for name in TEAM_ACCOUNTS}
    return set()


def update_team_status_table(readme_text: str, online_players: set[str]) -> str:
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

    team_names = {normalize_name(name) for name in TEAM_ACCOUNTS}
    online_team_members = online_players & team_names

    updated_table = [table_lines[0], table_lines[1]]
    for row in table_lines[2:]:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue

        role = cells[0]
        name = cells[1]
        status = "🟢 Online" if normalize_name(name) in online_team_members else "🔴 Offline"
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

    print(f"[INFO] Team-Status aktualisiert. Online Spieler: {len(online_players)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
