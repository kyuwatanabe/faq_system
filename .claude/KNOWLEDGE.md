# FAQシステム 開発ナレッジベース

このファイルには、開発作業でよく使うコマンドや手順を記録しています。

## プロジェクト概要

- **プロジェクト名**: GFアメリカビザサポートデスク FAQシステム
- **フレームワーク**: Flask (Python)
- **デプロイ先**: Railway
- **リポジトリ**: https://github.com/kyuwatanabe/faq_system.git

## よく使うコマンド

### サーバーの起動（ローカル）

```bash
cd "C:\Users\GF001\Desktop\システム開発\手引き用チャットボット\faq_system"
python web_app.py
```

サーバーが起動すると:
- ローカル: http://127.0.0.1:5000
- 管理画面: http://127.0.0.1:5000/admin

### Git操作

```bash
# 変更状況を確認
git status

# 変更をステージング
git add <ファイル名>

# コミット
git commit -m "コミットメッセージ"

# Railwayにプッシュ（自動デプロイ）
git push
```

### Railwayダッシュボードを開く

```bash
start https://railway.app/dashboard
```

または直接ブラウザで: https://railway.app/dashboard

### ブラウザキャッシュのクリア

HTMLやCSSの変更が反映されない場合:

1. **スーパーリロード**: `Ctrl + Shift + R`
2. **キャッシュクリア**: `Ctrl + Shift + Delete` → 「キャッシュされた画像とファイル」を削除
3. **完全リフレッシュ**: ブラウザを完全に閉じて再起動

## プロジェクト構造

```
faq_system/
├── web_app.py              # Flaskアプリのエントリーポイント
├── faq_system.py           # FAQシステムのコアロジック
├── faq_data-1.csv          # FAQデータ（本番データ）
├── pending_qa.csv          # 承認待ちQ&A
├── faq_generation_history.csv  # FAQ生成履歴（重複防止用）
├── templates/              # HTMLテンプレート
│   ├── index.html         # ユーザー向けFAQ検索画面
│   ├── admin.html         # 管理画面（FAQ一覧・編集・削除）
│   ├── add_faq.html       # FAQ追加画面
│   ├── auto_generate_faq.html  # FAQ自動生成画面
│   ├── review_pending.html     # 承認待ちFAQ確認画面
│   └── backup.html        # バックアップ管理画面
└── .claude/               # Claude Code用設定・ドキュメント
```

## 主要機能

1. **FAQ検索** (`/`) - ユーザーが質問を入力して回答を検索
2. **管理画面** (`/admin`) - FAQ一覧、編集、削除、まとめて削除
3. **FAQ追加** (`/admin/add_faq`) - 手動でFAQを追加
4. **FAQ自動生成** (`/admin/auto_generate_faq`) - PDFから自動生成
5. **承認待ちFAQ** (`/admin/review`) - 自動生成されたFAQを承認・却下
6. **バックアップ** (`/admin/backup`) - データのエクスポート・インポート

## 環境変数

- `CLAUDE_API_KEY`: Claude APIキー（オプション、自動生成機能で使用）
- `PORT`: ポート番号（デフォルト: 5000）

## デプロイフロー

1. ローカルで開発・テスト
2. `git add` → `git commit` → `git push`
3. RailwayがGitHubのプッシュを検知して自動デプロイ
4. 2〜3分後にデプロイ完了

## トラブルシューティングのポイント

- **HTMLの変更が反映されない** → ブラウザキャッシュをクリア
- **Pythonコードの変更が反映されない** → サーバーを再起動（Ctrl+C → 再度起動）
- **Railway上で反映されない** → `git push` を実行したか確認
- **フォームが動作しない** → フォームのネストがないか確認（開発者ツールでHTML構造を確認）
