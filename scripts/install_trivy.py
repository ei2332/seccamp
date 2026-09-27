"""Codespaces用Trivyを、固定バージョン・SHA256照合付きで導入する。"""

import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
from urllib.request import urlopen

VERSION = "0.74.0"
SHA256 = "2ae6fe3ee734b7fdf11335663e18c75ea12dccc76062f09f164a3b0f8be4371a"
URL = f"https://github.com/aquasecurity/trivy/releases/download/v{VERSION}/trivy_{VERSION}_Linux-64bit.tar.gz"
ROOT = Path(__file__).resolve().parents[1]


def install_archive(archive: Path, destination: Path):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("SHA256が一致しません。実行せず講師に知らせてください。")
    with tarfile.open(archive, "r:gz") as bundle:
        member = bundle.getmember("trivy")
        if not member.isfile():
            raise ValueError("通常ファイルのtrivyがありません。")
        source = bundle.extractfile(member)
        if source is None:
            raise ValueError("trivyを読み出せません。")
        # Archive paths are never extracted. Replace the executable only on success.
        with source, tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as out:
            staged = Path(out.name)
            try:
                shutil.copyfileobj(source, out)
                out.flush()
                staged.chmod(0o755)
                staged.replace(destination)
            finally:
                staged.unlink(missing_ok=True)


def main():
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise SystemExit("この導入手順はLinux x86_64のCodespaces用です。講師の比較結果で続行してください。")
    tools = ROOT / ".tools"
    tools.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lesson-trivy-") as temporary:
        archive = Path(temporary) / "trivy.tar.gz"
        print(f"Trivy {VERSION}を取得・照合します。", flush=True)
        with urlopen(URL, timeout=30) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)
        install_archive(archive, tools / "trivy")
    subprocess.run([str(tools / "trivy"), "--version"], check=True, timeout=10)
    print("導入完了。次はdocs/05-trivy.mdの事前準備でDBを取得します。")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, tarfile.TarError, KeyError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Trivy導入未完了: {error}\n再作成・課金はせず講師へ相談してください。") from error
