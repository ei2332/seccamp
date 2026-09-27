# 依存関係の管理

`requirements.txt`で直接依存を宣言し、`pylock.toml`で間接依存を含むバージョン・配布ファイル・SHA256を固定します。インストールとTrivy検査は同じ`pylock.toml`を使います。受講者が演習中にロックを作り直す必要はありません。

## 対象環境とインストール

このロックはCodespacesのLinux x86_64・Python 3.12で生成しています。macOS・Windows・別のPythonバージョンでの利用は保証しません。

Codespacesの初回構築とCIでは次の処理を自動で実行します。

```sh
python -m pip install pip==26.2.1
python -m pip install -r pylock.toml
python -m pip check
```

`pip lock`は25.1以降で利用できますが、`pip install -r pylock.toml`は26.1以降です。どちらも実験的機能のため、生成・インストールには検証済みのpip 26.2.1を使います。

移行前に作成したCodespaceでは、作業を保存してから最新の教材設定を取り込み、`Codespaces: Rebuild Container`で反映してください。講義中に再構築が難しい場合は、講師と確認のうえ既存の教材用仮想環境で上記コマンドを実行します。システムPythonへのsudoインストールはしません。

## 更新する場合（教材のメンテナンス用）

対象のCodespacesで`requirements.txt`を編集してから実行します。

```sh
python -m pip install pip==26.2.1
python -m pip lock -r requirements.txt -o pylock.toml
git diff -- requirements.txt pylock.toml
```

再生成では間接依存も更新される場合があります。差分・Trivyの結果を確認し、新しい仮想環境へのインストールと`pip check`、アプリの動作、pytest、Semgrepを検証してください。脆弱性修正前の教材では、pytestの2件の失敗とSemgrepの指摘3件が想定されます。

移行時は旧固定一覧を制約にして生成し、75パッケージのバージョンが一致することを確認しました。旧一覧は廃止し、以後の固定結果は`pylock.toml`を正とします。

参考：[pip lock](https://pip.pypa.io/en/stable/cli/pip_lock/)、[pip 26.1の変更](https://pip.pypa.io/en/stable/news/#v26-1)、[TrivyのPython対応](https://trivy.dev/docs/latest/guide/coverage/language/python/)。
