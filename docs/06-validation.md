# 現行教材の検証状況

2026-09-27、ローカルmacOSと新規2コアCodespaceで確認。pytest 9.1.1・Semgrep 1.178.0。

| 対象 | 初期コード | 別コピーに比較用修正を適用 |
|---|---|---|
| pytest全73件 | 71成功・2失敗 | SQL修正で73成功 |
| Semgrep p/owasp-top-ten（217ルール） | SQL・HTML生成・パストラバーサルの計3件 | SQL修正で2件残る |
| Semgrep SQLインジェクションの既存ルール | 1件・終了コード1 | 0件・終了コード0 |
| 選択課題のテスト2件 | 2失敗 | 追加2件も修正すると2成功 |

SemgrepはPython・JavaScript等の13ファイルを検査。JinjaのHTMLテンプレート14ファイルは`.semgrepignore`で除外し、解析警告なし・初期指摘3件を確認しました。SQL単独ルールはPython 9ファイルを検査します。通常テストの初期失敗は引用符を含む正当な検索と、SQLインジェクション入力による公開範囲の逸脱です。

以前の`p/python`による比較では、別コピーに`docs/04-fallback.md`のパラメータ化を適用し、73テスト成功・残り2件を確認済み。さらに選択課題も修正した比較版では75テスト成功・指摘0件を確認しました。これらは旧ルールセットでの記録です。配布用コードには修正を適用していません。

## 新規Codespacesでの確認

- Privateの検証用`scm2026-yamanashi-workshop`を現行教材へ更新し、SSH Featureなし・2コア・8GB RAM・32GB storageで新規起動。
- 環境確認スクリプト成功。Flask 3.1.3、pytest 9.1.1、Semgrep 1.178.0。
- 初期版で71テスト成功・2失敗。OWASPルールで3件・217ルール・13ファイル・解析警告なし。
- Copilot ChatのAgent／Autoへ修正条件を入力。app/main.pyだけにSQLのパラメータ化を提案。テスト・ルール・除外設定は変更なし。
- 独立に再検証し、73テスト成功、SQL単独ルール0件を確認。
- この確認は講師アカウントによるもの。Copilot Freeの利用枠・モデル・認証フローを実証したものではありません。

選択課題のHTML入力は`<b>見出し確認</b>`、パストラバーサルは一時フォルダの架空メモを使います。CSPは維持しており、HTML混入の確認をJavaScript実行の確認として扱いません。

必須CIは全体検査の結果表示とSQLインジェクションの合否判定を分けています。Private検証用リポジトリのPR #2で、実Codespacesから変更をpushし、両ジョブの成功・失敗・復旧を確認しました。配布元のmainには修正を入れていません。

| 状態 | コミット | PRのActions実行 | 結果 |
|---|---|---|---|
| SQL修正・CI導入 | `18b948e` | [36272203509](https://github.com/llamakko/scm2026-yamanashi-workshop/actions/runs/36272203509) | pytest・Semgrep成功 |
| 脆弱な検索へ戻す | `780ddab` | [36276415757](https://github.com/llamakko/scm2026-yamanashi-workshop/actions/runs/36276415757) | pytestは71成功・2失敗、SQL指摘1件でSemgrep失敗 |
| 修正済みへ復旧 | `2c253da` | [36276517382](https://github.com/llamakko/scm2026-yamanashi-workshop/actions/runs/36276517382) | pytest・Semgrep成功 |

復旧時のPR実行は2026-09-26 22:30:45–22:31:10 UTCの約25秒。説明・操作・受講者の待ち時間は含みません。PRは未マージです。

## SARIF Viewerの実動作（2026-09-27）

- devcontainerの拡張機能に`MS-SarifVSCode.sarif-viewer`を追加。今回はファイルを直接開くため、`sarif-viewer.connectToGithubCodeScanning`は`off`に設定。
- 起動済みのPrivate検証用CodespaceへSARIF Viewer 3.4.5を手動インストールし、ブラウザ版VS Codeで確認。
- SQL修正済みの`lesson`ブランチ（`18b948e`）で`semgrep scan --config p/owasp-top-ten --sarif-output /tmp/semgrep-after.sarif app/`を実行。217ルール・13ファイル・残り2件。SARIFのバージョンは2.1.0。
- `code /tmp/semgrep-after.sarif`で自動的にSARIF Resultsが開き、HTML文字列生成とパストラバーサルの2件を表示。各指摘の説明とルールID、および`app/travel_tools.py`の14行目・25行目への移動を確認。
- GitHub Code Scanningとの接続やSARIFアップロードは不要。新しいdevcontainer設定による自動インストールと接続案内の抑止は、まだ再構築で確認していません。

## テストデータ

- 各テストは一時DBを作成し、画面用サンプルを投入せず、`tests/conftest.py` で専用の利用者・グループ・プランを登録します。
- テストで使用するID・タイトルはテスト側で定義したデータです。ローカルプレビューのDBは読み書きしません。
- 登録・入力エラー時の件数は操作前後で比較します。画面用サンプルのタイトルや旅程の件数は機能テストの期待値にしません。
- 入力検証は正常なデータで保存できることを確認したうえで、対象項目を不正値に変更します。
- 再初期化後も、保存したプラン・旅程・設定・グループ参加・お気に入りが維持されることを確認します。
- 権限、入力検証、CSRF、HTMLエスケープ等の検証はアプリ全体の安全性を保証するものではありません。

## 残る確認

- 新しく作った受講者リポジトリでの起動。旅行サービス版はmainへ反映済み。
- 実Codespaces・Copilot Free・GitHub Actionsでの一連の操作と所要時間。
- スライド・講師台本と現行教材の整合、およびビルド後の表示確認。

公開設定は変更していません。

## pylock.tomlへの移行（2026-09-27、日本時間）

以下は3種類の検出を追加する前の検証記録です。

実Codespace（Linux x86_64・Python 3.12.11）の一時ディレクトリに新しい仮想環境を作り、pip 26.2.1で生成・インストールを確認しました。既存の教材用仮想環境は変更していません。

- 旧固定一覧を制約にして生成し、75パッケージの名前・バージョンが一致。配布ファイルのSHA256も全パッケージに記録。
- `pip install -r pylock.toml`と`pip check`が成功。`scripts/check_environment.py`も成功。
- 初期コード：pytestは63成功・想定どおり2失敗。Semgrepは151ルール・8ファイル・SQLインジェクションの指摘1件。
- 一時コピーに比較用のパラメータ化修正を適用：pytestは65成功、Semgrepの指摘0件。配布するアプリのコードは変更していません。
- Trivy 0.74.0：Target=`pylock.toml`、Type=`pylock`、75パッケージ、指摘0件。DB更新日時は2026-09-26 12:58:40 UTC。

DockerfileとCI雛形も同じpip・ロックを使うよう更新しました。今回の検証は実Codespace内の新規仮想環境によるもので、変更後のdevcontainer全体の再構築やGitHub Actionsでの実行は未確認です。Dockerデーモンは利用できなかったため、イメージビルド成功とは扱っていません。
