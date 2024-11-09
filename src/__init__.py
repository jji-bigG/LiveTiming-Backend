from pathlib import Path
import sys

src_path = str(Path(__file__).parent.absolute())
if src_path not in sys.path:
    sys.path.append(src_path)
