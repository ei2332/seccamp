"""環境の準備を確認する。演習のセキュリティ検査はまだ実行しない。"""

from importlib.metadata import version
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import create_app  # noqa: E402


def main():
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12の環境で実行してください。")
    for name in ("Flask", "pytest", "semgrep"):
        print(f"{name}: {version(name)}")
    if not shutil.which("semgrep"):
        raise SystemExit("semgrepが見つかりません。仮想環境またはコンテナの作成ログを確認してください。")
    if not shutil.which("gh"):
        raise SystemExit("GitHub CLIが見つかりません。コンテナの作成ログを講師と確認してください。")
    # 利用者が保存したプランを変更せず、独立した架空データで確認する。
    with TemporaryDirectory(prefix="travel-check-") as folder:
        app = create_app({"DATABASE": str(Path(folder) / "check.sqlite3")})
        with app.test_client() as client:
            response = client.get("/", query_string={"q": "山梨"})
            if response.status_code != 200 or "山梨で湖とカフェを巡る週末" not in response.get_data(as_text=True):
                raise SystemExit("アプリの起動確認に失敗しました。講師に画面を見せてください。")
    print("準備完了: python scripts/start_app.py でアプリを起動できます。")
    print("次の手順: docs/01-start-and-scan.md")


if __name__ == "__main__":
    main()
