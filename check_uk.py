import sys
from pathlib import Path
from scripts.checks import ukrainian

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_uk.py <file-path>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    content = path.read_text()
    results = ukrainian.run_all(content, path)
    
    for r in results:
        status = "✅" if r.passed else "❌"
        print(f"{status} [{r.check}] {r.message}")

if __name__ == "__main__":
    main()
