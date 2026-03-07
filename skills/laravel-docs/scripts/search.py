#!/usr/bin/env python3
"""
Laravel Documentation Search Tool

Searches the official Laravel ecosystem documentation via the boost.laravel.com API.
Auto-detects Laravel version from composer.json and scopes results accordingly.

Usage:
    python search.py "routing" "middleware" --token-limit 3000 --dir /path/to/project
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

API_URL = "https://boost.laravel.com/api/docs"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0 Laravel-Docs-Skill"

KNOWN_PACKAGES = {
    "laravel/cashier": "laravel/cashier",
    "laravel/cashier-paddle": "laravel/cashier-paddle",
    "laravel/folio": "laravel/folio",
    "laravel/framework": "laravel/framework",
    "laravel/horizon": "laravel/horizon",
    "laravel/mcp": "laravel/mcp",
    "laravel/octane": "laravel/octane",
    "laravel/passport": "laravel/passport",
    "laravel/pennant": "laravel/pennant",
    "laravel/pint": "laravel/pint",
    "laravel/pulse": "laravel/pulse",
    "laravel/reverb": "laravel/reverb",
    "laravel/sail": "laravel/sail",
    "laravel/scout": "laravel/scout",
    "laravel/socialite": "laravel/socialite",
    "laravel/wayfinder": "laravel/wayfinder",
    "laravel/ai": "laravel/ai",
    "laravel/breeze": "laravel/breeze",
    "laravel/jetstream": "laravel/jetstream",
    "laravel/fortify": "laravel/fortify",
    "laravel/sanctum": "laravel/sanctum",
    "laravel/telescope": "laravel/telescope",
    "laravel/nova": "laravel/nova",
    "laravel/spark": "laravel/spark",
    "livewire/livewire": "livewire/livewire",
    "livewire/flux": "livewire/flux",
    "livewire/flux-pro": "livewire/flux-pro",
    "livewire/volt": "livewire/volt",
    "inertiajs/inertia-laravel": "inertiajs/inertia-laravel",
    "filament/filament": "filament/filament",
    "pestphp/pest": "pestphp/pest",
    "phpunit/phpunit": "phpunit/phpunit",
}


def normalize_version(version: str) -> str:
    """
    Normalize a composer version string to major.x format.
    
    Examples:
        "11.42.0" -> "11.x"
        "^10.0" -> "10.x"
        "v12.0.0" -> "12.x"
        "3.x-dev" -> "3.x"
    """
    version = version.lstrip("^~v")
    parts = version.split(".")
    if parts and parts[0].isdigit():
        return f"{parts[0]}.x"
    return "0.x"


def detect_packages_from_composer(composer_path: Path) -> list[dict]:
    """
    Parse composer.json and extract known Laravel ecosystem packages.
    
    Returns list of {name, version} dicts for packages we know the docs support.
    Packages are sorted so laravel/* packages come first.
    """
    if not composer_path.exists():
        return []
    
    try:
        with open(composer_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    
    packages = []
    require = data.get("require", {})
    require_dev = data.get("require-dev", {})
    all_deps = {**require, **require_dev}
    
    for dep_name, dep_version in all_deps.items():
        normalized_name = dep_name.lower()
        if normalized_name in KNOWN_PACKAGES:
            packages.append({
                "name": KNOWN_PACKAGES[normalized_name],
                "version": normalize_version(dep_version)
            })
    
    def sort_key(pkg: dict) -> tuple:
        name = pkg.get("name", "")
        is_laravel = name.startswith("laravel/")
        return (0 if is_laravel else 1, name)
    
    packages.sort(key=sort_key)
    
    return packages


def search_docs(
    queries: list[str],
    packages: Optional[list[dict]] = None,
    token_limit: int = 3000,
) -> str:
    """
    Send a search request to the Laravel docs API.
    
    Args:
        queries: List of search query strings
        packages: Optional list of {name, version} dicts. If empty, searches all packages.
        token_limit: Maximum tokens in response (default 3000, max 1000000)
    
    Returns:
        Markdown-formatted documentation text
    """
    cleaned_queries = [q.strip() for q in queries if q.strip()]
    if not cleaned_queries:
        return "Error: No valid queries provided."
    
    payload = {
        "queries": cleaned_queries,
        "packages": packages if packages else [],
        "token_limit": min(token_limit, 1000000),
        "format": "markdown"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers=headers,
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "Unknown error"
        return f"HTTP Error {e.code}: {error_body}"
    except urllib.error.URLError as e:
        return f"Network Error: {e.reason}"
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(
        description="Search Laravel ecosystem documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "routing"
    %(prog)s "middleware groups" "authentication" --token-limit 5000
    %(prog)s "livewire components" --dir /path/to/laravel/project
        """
    )
    parser.add_argument(
        "queries",
        nargs="+",
        help="One or more search queries"
    )
    parser.add_argument(
        "--token-limit", "-t",
        type=int,
        default=3000,
        help="Maximum tokens in response (default: 3000, max: 1000000)"
    )
    parser.add_argument(
        "--dir", "-d",
        type=Path,
        default=Path.cwd(),
        help="Project directory containing composer.json (default: current directory)"
    )
    parser.add_argument(
        "--package", "-p",
        action="append",
        metavar="NAME:VERSION",
        help="Manually specify a package (e.g., 'laravel/framework:11.x'). Can be used multiple times."
    )
    
    args = parser.parse_args()
    
    packages = None
    
    if args.package:
        packages = []
        for pkg_spec in args.package:
            if ":" in pkg_spec:
                name, version = pkg_spec.rsplit(":", 1)
                packages.append({"name": name, "version": version})
            else:
                print(f"Warning: Invalid package format '{pkg_spec}'. Use 'name:version'.", file=sys.stderr)
    else:
        composer_path = args.dir / "composer.json"
        packages = detect_packages_from_composer(composer_path)
        if packages:
            package_list = ", ".join(f"{p['name']}@{p['version']}" for p in packages)
            print(f"Detected packages: {package_list}", file=sys.stderr)
        else:
            print("No Laravel packages detected in composer.json, searching all available packages.", file=sys.stderr)
    
    result = search_docs(
        queries=args.queries,
        packages=packages,
        token_limit=args.token_limit,
    )
    
    print(result)


if __name__ == "__main__":
    main()
