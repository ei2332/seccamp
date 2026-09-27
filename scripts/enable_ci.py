"""演習用CIを追加する。既存のワークフローは上書きしない。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "stages" / "02-ci" / "checks.yml"
    destination = ROOT / ".github" / "workflows" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_text(encoding="utf-8")
    try:
        with destination.open("x", encoding="utf-8") as target:
            target.write(content)
    except FileExistsError:
        print("checks.ymlは追加済みです。既存の内容は変更していません。")
        return
    print(".github/workflows/checks.ymlを追加しました。内容を確認しましょう。")


if __name__ == "__main__":
    main()
