#!/usr/bin/env python3
"""
Fragt den Online-Status des Cookie SMP Servers ab und schreibt eine
aktuelle Team-Status-Tabelle zwischen die Marker in der README.md.

Benoetigt: pip install mcstatus
"""

import re
import sys
from datetime import datetime, timezone

from mcstatus import JavaServer

SERVER_ADDRESS = "cookie-smp.minecraft.party"
README_PATH = "README.md"

# Rolle -> Minecraft-Name. Reihenfolge bestimmt die Reihenfolge in der Tabelle.
TEAM = [
    ("Owner", "Kecks_Kruemmel"),
    ("Manager", "Jecrafter"),
    ("Admin", "Drr_Benjii"),
    ("Developer", "Tobias86825"),
    ("Moderator", "Staffcrafter"),
    ("Moderator", "DDR_Maik"),
]

START_MARKER = "<!-- TEAM-STATUS:START -->"
END_MARKER = "<!-- TEAM-STATUS:END -->"


def get_online_players() -> set[str]:
    """Fragt den Server per Java-Query ab. Gibt bei Fehlern eine leere Menge zurueck."""
    try:
        server = JavaServer.lookup(SERVER_ADDRESS)
        status = server.status()
        if not status.players.sample:
            return set()
        return {p.name for p in status.players.sample}
    except Exception as exc:  # Server offline, Timeout, etc.
        print(f"Konnte Serverstatus nicht abfragen: {exc}", file=sys.stderr)
        return set()


def build_table(online_players: set[str]) -> str:
    rows = [
        "| Rolle | Name | Status |",
        "| ----- | ---- | ------ |",
    ]
    for role, name in TEAM:
        online = name in online_players
        status = "🟢 Online" if online else "🔴 Offline"
        rows.append(f"| {role} | {name} | {status} |")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows.append("")
    rows.append(f"_Zuletzt aktualisiert: {timestamp}_")
    return "\n".join(rows)


def update_readme(table: str) -> bool:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{table}\n{END_MARKER}"

    if not pattern.search(content):
        print("Marker nicht gefunden, README wird nicht veraendert.", file=sys.stderr)
        return False

    new_content = pattern.sub(replacement, content)

    if new_content == content:
        return False

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


def main() -> None:
    online_players = get_online_players()
    table = build_table(online_players)
    changed = update_readme(table)
    print("README aktualisiert." if changed else "Keine Aenderung noetig.")


if __name__ == "__main__":
    main()
