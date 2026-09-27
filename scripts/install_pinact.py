"""CodespacesとCIに、バージョンとSHA256を固定したpinactを導入する。"""

import hashlib
import io
from pathlib import Path
import platform
import tarfile
import urllib.error
import urllib.request

VERSION = "5.0.0"
# 公式v5.0.0リリースのchecksums.txtと照合。
CHECKSUMS = {
    "x86_64": ("amd64", "d005bbb85da80dacdc07816f24a5da723a9f6d1e9f3d3e7e73df33f9caa1358f"),
    "aarch64": ("arm64", "d28ca5e9ddd7950da4a808288f8a83f84fc3ca40e86bab970f3adeef33578c0b"),
}
ROOT = Path(__file__).resolve().parents[1]


def main():
    machine = platform.machine()
    if platform.system() != "Linux" or machine not in CHECKSUMS:
        raise SystemExit("この演習はLinuxのCodespacesで実行してください。")
    arch, expected = CHECKSUMS[machine]
    url = (
        f"https://github.com/suzuki-shunsuke/pinact/releases/download/v{VERSION}/"
        f"pinact_linux_{arch}.tar.gz"
    )
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        raise SystemExit(f"pinactを取得できませんでした。接続を確認してください: {error}") from error
    if hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit("SHA256が一致しません。インストールを中止しました。")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.getmember("pinact")
        if not member.isfile():
            raise SystemExit("配布物に通常ファイルのpinactがありません。")
        with archive.extractfile(member) as source:
            binary = source.read()
    destination = ROOT / ".tools" / "pinact"
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(binary)
    destination.chmod(0o755)
    print(f"pinact v{VERSION}を.tools/pinactに配置しました。")


if __name__ == "__main__":
    main()
