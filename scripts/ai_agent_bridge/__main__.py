"""Allow running as script or package: python scripts/ai_agent_bridge/__main__.py"""

import sys
from pathlib import Path

# When run directly as a script, add scripts/ to path so the package is importable
if __name__ == "__main__":
    scripts_dir = str(Path(__file__).resolve().parent.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge._cli import main
    main()
else:
    # When imported as part of the package (python -m ai_agent_bridge)
    from ._cli import main
    main()
