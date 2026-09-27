"""Stop the app first. Move demo data to a unique backup, never delete it."""

import argparse
import shutil
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="演習データをバックアップして初期化します。先にアプリを停止してください。")
    parser.add_argument("--confirm", action="store_true", help="停止済みであることを確認して実行")
    args = parser.parse_args()
    if not args.confirm:
        parser.error("アプリを停止し、--confirmを指定してください。")
    instance = Path(__file__).resolve().parents[1] / "instance"
    database = instance / "travel.sqlite3"
    if not database.exists():
        print("保存済みデータはありません。次回の起動時に初期データを作成します。")
        return
    backups = instance / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix="travel-", dir=backups))
    for suffix in ("", "-wal", "-shm", "-journal"):
        source = Path(str(database) + suffix)
        if source.exists():
            shutil.move(str(source), str(target / source.name))
    print(f"バックアップ: {target}")
    print("次回の起動時に初期データを作成します。")


if __name__ == "__main__":
    main()
