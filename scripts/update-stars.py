"""Refresh existing star-count markers in both profile translations."""

import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
FILES = (ROOT / "README.md", ROOT / "README.en.md")
MARKER = re.compile(r"(<!--stars:([A-Za-z0-9_.-]+)-->)([0-9]+)(<!--/stars-->)")


def main():
    originals = {path: path.read_text(encoding="utf-8") for path in FILES}
    repositories = sorted({match[1] for text in originals.values() for match in MARKER.findall(text)})
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "StoneLL1-profile"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    counts = {}
    for repository in repositories:
        request = Request(f"https://api.github.com/repos/StoneLL1/{repository}", headers=headers)
        with urlopen(request, timeout=30) as response:
            metadata = json.load(response)
        if metadata.get("private") or metadata.get("fork"):
            raise ValueError(f"Expected an original public repository: {repository}")
        count = metadata["stargazers_count"]
        if type(count) is not int or count < 0:
            raise ValueError(f"Invalid star count: {repository}")
        counts[repository] = count

    # Fetch and validate all metadata before changing either translation.
    for path, original in originals.items():
        updated = MARKER.sub(lambda match: f"{match[1]}{counts[match[2]]}{match[4]}", original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            print(f"Updated {path.name}")
    print(f"Checked {len(counts)} public projects across {len(FILES)} translations.")


if __name__ == "__main__":
    main()
