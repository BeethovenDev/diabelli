"""DIABELLI — file integrity watch.

Named after Beethoven's 33 Variations on a waltz by Anton Diabelli: one humble
theme, thirty-three transformations. DIABELLI takes one tree and watches how it
changes — every added, removed and modified file accounted for, each guarded by
a SHA-256 fingerprint.

Diabelli's variations were never chained into anything; theirs must be. Run
``diabelli init`` once, then let ``diabelli check`` (in CI) or ``diabelli
watch`` (locally) be the variation you can trust.
"""

from __future__ import annotations

__version__ = "0.1.0"

BANNER = r"""
   ____ ____  _    ___  _     _   _ _____
  / ___|  _ \| |  | \ \/ /   | | | | ____|
 | |  _| |_) | |__| |\  / _  | | | |  _|
 | |_| |  _ <|  __  |/  \| |_| | |_| |___
  \____|_| \_\_|  |_/_/\_\\___/ \___/|_____|

        file integrity — thirty-three variations on one theme
"""

__all__ = ["BANNER", "__version__"]
