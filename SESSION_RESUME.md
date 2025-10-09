# FAQ自動生成システム - セッション再開ガイド

## 現在の状況

### 完了した作業
1. **重複FAQ生成問題の修正** ✅
   - 問題：同じ質問が繰り返し生成される
   - 原因：Claude APIにAPI keyが渡されず、モックFAQが使用されていた
   - 解決策：web_app.py Line 13でAPI keyをFAQSystemインスタンスに渡す

2. **プロンプト改善** ✅
   - 既存質問を★マーカー付きでプロンプトの上部に配置
   - faq_system.py Line 732-748を修正

3. **重複防止機能の検証** ✅
   - Railway本番環境で10ラウンド×10問＝102件生成
   - 重複なしを確認
   - ログで `[DEBUG] ユニークな既存質問: 98件` が累積的に増加することを確認

### 未完了の作業（次回やること）

**最優先：FAQ品質チェック** ❌
- 現状：重複しないことは確認したが、生成されたFAQの内容が適切かは未確認
- やること：
  1. Railway本番環境の承認待ちFAQを全削除
  2. FAQ自動生成を3-5回実行（第2章.pdfで各10問）
  3. 生成された質問が第2章.pdfの内容に基づいているか確認
  4. 問題があればプロンプトを調整

## 修正したファイル

### web_app.py
**Line 13** - API keyをFAQSystemに渡す
```python
app = Flask(__name__)
faq_system = FAQSystem('faq_data-1.csv')
faq_system.claude_api_key = os.getenv('CLAUDE_API_KEY')  # ← この行を追加
```

### faq_system.py

**Line 17** - API key用のインスタンス変数追加
```python
def __init__(self, csv_file):
    self.csv_file = csv_file
    self.claude_api_key = None  # web_app.pyから設定される ← この行を追加
```

**Line 699** - API key取得ロジック修正
```python
def generate_faqs_from_document(self, pdf_path, num_questions=3, category='一般'):
    # ...
    api_key = self.claude_api_key or os.getenv('CLAUDE_API_KEY')  # ← 修正
    print(f"[DEBUG] CLAUDE_API_KEY check: {'SET' if api_key else 'NOT SET'}")
    if api_key:
        print(f"[DEBUG] API key starts with: {api_key[:10]}...")
    if not api_key:
        print("[ERROR] CLAUDE_API_KEY未設定。モック生成機能を使用します...")
        return self._mock_faq_generation(num_questions, category)
```

**Line 732-748** - プロンプト構造変更
```python
# 既存質問のコンテキスト作成
if unique_questions:
    existing_context = "【重要：以下の★既存質問は絶対に生成しないこと】\n\n"
    existing_context += "\n".join([f"★既存質問{i+1}: {q}" for i, q in enumerate(unique_questions[:100])])
    existing_context += "\n\n上記の★既存質問と意味が重複する質問は絶対に生成しないでください。"
else:
    existing_context = "既存の質問はありません。"

# プロンプト作成
prompt = f"""
あなたはアメリカビザ専門のFAQシステムのコンテンツ生成エキスパートです。

{existing_context}

【タスク】
上記の★既存質問と意味が重複しない、完全に異なるトピックのFAQを以下のPDFドキュメントから{num_questions}個生成してください。
```

## 次回の再開手順

### Step 1: 環境確認
```bash
cd "C:\Users\GF001\Desktop\システム開発\手引き用チャットボット\faq_system"
git status  # 変更がないことを確認
```

### Step 2: Railway本番環境でFAQ品質チェック

1. **承認待ちFAQをクリア**
   - URL: https://faqsystem-production.up.railway.app/admin/review
   - 全選択 → 一括却下

2. **FAQ自動生成を3-5回実行**
   - URL: https://faqsystem-production.up.railway.app/admin/auto_generate_faq
   - ファイル: `reference_docs/第2章.pdf`
   - 質問数: 10
   - カテゴリ: AI生成
   - これを3-5回繰り返す

3. **生成されたFAQを確認**
   - URL: https://faqsystem-production.up.railway.app/admin/review
   - チェックポイント：
     - [ ] 質問が第2章.pdfの内容（ビザ、I-94、滞在期限、オーバーステイ等）に基づいているか
     - [ ] 無関係な質問（他の章の内容、全く関係ない話題）が混ざっていないか
     - [ ] 回答が正確で適切な長さか
     - [ ] キーワードが適切に抽出されているか

### Step 3: 問題があった場合の対応

**問題パターン1: 第2章と無関係な質問が生成される**
→ faq_system.py Line 750-780のプロンプトに「PDFドキュメントの内容のみに基づく」を強調

**問題パターン2: 回答が不正確**
→ プロンプトに「回答は必ずPDFの記載内容に基づくこと」を追加

**問題パターン3: 質問が抽象的すぎる/具体的すぎる**
→ プロンプトの質問例を調整

## 検証データ

### 直前の10ラウンドテスト結果
- 合計: 102件のFAQ生成
- 重複: なし
- JSON parse error: 2回（Round 3, 6）→ モックFAQにフォールバック
- 既存質問認識数の推移: 0 → 10 → 20 → 30 → ... → 117件

### ログから確認できた質問例
- "アメリカのNAFTA専門職ビザTNビザ"
- "オーストラリア人がアメリカで就労する際のビザ"
- "アメリカ留学中にアルバイトをすることはできますか?"
- "アメリカのDビザとはどのようなビザですか?"
- "NATO関連ビザにはどのようなものがありますか?"

### 最新生成の3件（参考用）
1. Q: アメリカの企業内転勤ビザ(L-1ビザ)の取得条件と申請プロセスは?
2. Q: アメリカの短期ビジネス訪問に必要なB-1ビザとはどのようなビザですか?
3. Q: アメリカへの一時的な入国にはESTA申請が必要ですか?

## 技術的な残課題（優先度低）

### JSON parse error対策
- 発生頻度: 10回中2回
- 原因: Claude APIレスポンス内の制御文字（改行等）
- 現在の対処: モックFAQへのフォールバック
- 改善案: faq_system.py Line 851-893のクリーニング処理を強化

## 参考情報

### 関連URL
- Railway本番環境: https://faqsystem-production.up.railway.app
- 管理画面: https://faqsystem-production.up.railway.app/admin
- FAQ自動生成: https://faqsystem-production.up.railway.app/admin/auto_generate_faq
- 承認待ち一覧: https://faqsystem-production.up.railway.app/admin/review

### 重要なファイル
- `web_app.py` - Flaskアプリ本体、Line 13でAPI key設定
- `faq_system.py` - FAQ生成ロジック、Line 732-748がプロンプト
- `faq_generation_history.csv` - 生成履歴（重複防止用）
- `pending_qa.csv` - 承認待ちFAQ
- `faq_data-1.csv` - 承認済みFAQ

### GitHubリポジトリ
- URL: https://github.com/kyuwatanabe/faq_system.git
- 最新コミット: "Clean: 不要なテストファイルと一時ファイルを削除"
