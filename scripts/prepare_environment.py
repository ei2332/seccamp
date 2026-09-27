"""必須環境を確認し、ミニ演習用のTrivyとDBを時間制限付きで準備する。"""

from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, "scripts/check_environment.py"], cwd=ROOT, check=True)
    print("続いてTrivyを準備します（最大約2分）。", flush=True)
    try:
        if shutil.disk_usage(ROOT).free < 2 * 1024**3:
            raise OSError("TrivyのDB用に2GB以上の空き容量が必要です。")
        subprocess.run(
            [sys.executable, "scripts/install_trivy.py"], cwd=ROOT, check=True, timeout=60
        )
        subprocess.run(
            [str(ROOT / ".tools/trivy"), "image", "--download-db-only",
             "--disable-telemetry", "--cache-dir", ".tools/trivy-cache", "--timeout", "1m"],
            cwd=ROOT, check=True, timeout=70,
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(f"Trivyの準備は未完了: {error}", flush=True)
        print("他の演習は続行できます。Trivyの時間に講師へ知らせてください。")
        print("再試行手順: docs/05-trivy.md")
    else:
        print("Trivyの準備完了（アプリの検査はまだ実行していません）。")
    print("環境準備を終了しました。講師の案内に合わせてdocs/01-start-and-scan.mdへ進みます。")


if __name__ == "__main__":
    main()
