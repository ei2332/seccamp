# CIの雛形

Codespacesで`python scripts/enable_ci.py`を実行すると、`checks.yml`を`.github/workflows/`へコピーします。既存ファイルは上書きしません。

[CI導入手順](../../docs/03-ci.md)に沿って使ってください。

- `pytest`と`semgrep`は独立したジョブとして実行します。
- Semgrepは`p/owasp-top-ten`の全指摘をログに表示し、必須演習で修正するSQLインジェクションの既存ルールを合否判定に使います。選択課題の2件はCI成功後も残るため、Issueで管理します。
- 必須CIは`pytest`と`semgrep`だけです。SHA固定は補足に移し、意図的に失敗するジョブは設けません。
- 雛形は`stages/`に置いてある間は実行されません。pinactにはコピー先のファイルを明示します。
- Actionのバージョンは演習用の出発点として指定しています。最新版を意味しません。更新する場合は公式の変更履歴と差分を確認します。

pinact v5.0.0の[公式配布物](https://github.com/suzuki-shunsuke/pinact/releases/tag/v5.0.0)を使用します。導入スクリプトのSHA256は同リリースの`pinact_5.0.0_checksums.txt`と照合した値です。SHA256は配布物の取り違えや変更の検出に使うもので、ツールの安全性を保証するものではありません。
