# ミニ演習：Trivyで依存関係を調べる

第2章の5分。自分たちのコードを調べるSASTに加え、利用する部品の既知の脆弱性を調べるSCAを体験します。操作場所は自分のCodespacesのターミナル、リポジトリのルートです。依存の更新やCIへのTrivy追加は必須課題にしません。

## 準備の確認

新しいCodespacesでは、初回起動時にTrivyとDBを自動で準備します。「Trivyの準備完了」が表示されたら、手順1へ進んでください。アプリの検査はまだ実行していません。

準備が未完了の場合や、以前に作ったCodespaceを使う場合だけ、次を実行します。

```sh
python scripts/install_trivy.py
.tools/trivy image --download-db-only --disable-telemetry --cache-dir .tools/trivy-cache --timeout 1m
```

導入スクリプトはLinux x86_64用Trivy v0.74.0を公式リリースから取得し、教材に固定したSHA256を照合してから`.tools/trivy`へ配置します。sudo・PAT・支払い情報は不要です。すでにCodespaceを使っている人もコンテナの再作成は不要です。

DBの圧縮ダウンロードは検証時約118MiB、展開後のキャッシュは約1.4GBでした。無料ストレージ残量を確認し、不足時は講師の比較結果で参加してください。`--download-db-only`はDBの準備だけで、アプリを検査したことにはなりません。

1分程度で準備が終わらない、認証・通信・容量エラーが出る場合は、繰り返し作り直さず講師へ知らせてください。

## 1. 何を調べるか

`pylock.toml`を開き、Flaskなどの名前と固定バージョンを確認します。このロックファイルは間接依存や検査ツールの依存も含み、検証時は75パッケージでした。

`requirements.txt`は直接依存3件の宣言、`pylock.toml`はインストールに使う依存関係の固定結果です。Trivyは`pylock.toml`を標準で認識するため、ファイル名の追加指定は不要です。アプリのSQL処理やOS全体を調べるコマンドではありません。

## 2. 検査する

```sh
.tools/trivy fs --scanners vuln --disable-telemetry \
  --cache-dir .tools/trivy-cache --timeout 1m pylock.toml
```

**完了の目印：** Report SummaryのTargetが`pylock.toml`、Typeが`pylock`で、Vulnerabilitiesの結果が表示される。

- `0`：この対象・バージョン・DBでは既知の脆弱性の指摘なし。安全の保証ではない
- 指摘あり：ライブラリ名、Installed Version、Vulnerability ID、Severity、Fixed Versionを確認。修正版の有無や自分の使い方への影響を調べる
- 対象なし・`-`・エラー・時間切れ：検査完了としない

対象・結果・未確認事項を短くメモします。この時点ではIssue・PRはまだ作りません。問題があれば後で検索の不具合とは別の課題として記録します。DBの更新で結果が変わるので、講師と同じ件数に合わせる必要はありません。

## 3. 検査範囲を説明する

「依存ライブラリに既知の脆弱性の指摘がなかった」と「公開プラン検索のSQLが安全」は別の確認です。今回Trivyは後者を確認していません。

指摘があっても、この5分で一律に最新バージョンへ更新しません。更新の影響を調べ、テストして判断する作業を次の行動として残します。このコマンドは結果を読むためのものです。指摘をCIの失敗にする設定は含みません。

## 時間内に実行できない場合

1分で終わらなければCtrl+Cで中断し、次の講師の結果を読みます。自分の実行とは区別して「未完了、講師結果で確認」と記録してください。

| 2026-09-27（日本時間）の講師による検証 | 結果 |
|---|---|
| 環境 | 2コアCodespaces、Trivy 0.74.0 |
| 対象 | pylock.toml、75パッケージ |
| DB更新日時 | 2026-09-26 12:58:40 UTC |
| 既知の脆弱性の指摘 | 0件 |
| 初回検査 | DB取得を含め約9秒。操作・説明時間を除く |

現行教材と同じ75パッケージを固定した`pylock.toml`を、実Codespaceの一時環境で検査した結果です。当日の通信速度やDBの結果を保証するものではありません。ロックの更新方法は[依存関係の管理](07-dependencies.md)を参照してください。

## 終了後

`.tools/`はGit管理対象外で、バイナリ・DBをcommitする必要はありません。キャッシュはCodespace停止後も保存容量を使います。不要になったDBだけを削除する場合は次を実行します。後日の検査では再取得が必要です。

```sh
.tools/trivy clean --cache-dir .tools/trivy-cache --vuln-db
```

演習はこのあとも続きます。Codespaceは停止せず、講師の案内を待ってください。

参考：[Python対応範囲](https://trivy.dev/docs/latest/guide/coverage/language/python/)、[固定リリース](https://github.com/aquasecurity/trivy/releases/tag/v0.74.0)。
