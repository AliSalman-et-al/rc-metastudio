"""Remove build-only R payload from a disposable package staging tree."""

from pathlib import Path
import argparse
import shutil


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("home", type=Path)
    parser.add_argument("closure", type=Path)
    parser.add_argument("--windows", action="store_true")
    args = parser.parse_args()
    home = args.home.resolve(strict=True)
    library = home / "library"
    keep = set(args.closure.read_text(encoding="utf-8-sig").splitlines())
    if "RCMetaR" not in keep or not all((library / name / "DESCRIPTION").is_file() for name in keep):
        raise SystemExit("Closure is empty or does not match the staged library")
    if args.windows and "tcltk" in keep:
        raise SystemExit("Cannot remove Tcl: dependency closure requires tcltk")
    removed = 0

    def remove(path: Path) -> None:
        nonlocal removed
        if path.is_symlink():
            raise SystemExit(f"Refusing to prune symlink: {path}")
        if path.exists():
            size = sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.is_dir() else path.stat().st_size
            print(f"Removing {path.relative_to(home)}: {size} bytes")
            removed += size
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    for package in sorted(library.iterdir()):
        if not package.is_dir():
            continue
        if package.name not in keep:
            remove(package)
            continue
        for name in ("tests", "demo", "testdata", "tinytest", "help", "html", "doc", "vignettes", "include"):
            remove(package / name)
    for path in (library / "RCMetaR" / "qa", home / "doc", home / "include"):
        remove(path)
    if args.windows:
        for name in ("Tcl", "bin/i386", "modules/i386"):
            remove(home / name)
    print(f"Removed {removed} staged R bytes; retained {len(keep)} packages")


if __name__ == "__main__":
    main()
