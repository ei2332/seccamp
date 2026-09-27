"""演習アプリを起動。debug・自動リロードは無効、loopbackだけで待ち受ける。"""

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.execv(sys.executable, [
    sys.executable, "-m", "flask", "--app", "app.main:create_app", "run",
    "--host", "127.0.0.1", "--port", "5000", "--no-debug", "--no-reload",
])
