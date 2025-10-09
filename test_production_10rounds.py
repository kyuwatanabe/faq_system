import requests
import time
import os

BASE_URL = "https://faqsystem-production.up.railway.app"
ROUNDS = 10
QUESTIONS_PER_ROUND = 10
PDF_PATH = "reference_docs/第2章.pdf"

print("FAQ自動生成テスト開始（本番環境）")
print(f"URL: {BASE_URL}")
print(f"ラウンド数: {ROUNDS}")
print(f"1ラウンドあたりの質問数: {QUESTIONS_PER_ROUND}")
print("="*60)

# 承認待ちFAQをクリア
print("\n承認待ちFAQをクリア中...")
response = requests.post(f"{BASE_URL}/admin/batch_delete_pending", json={'qa_ids': 'all'})
if response.status_code == 200:
    print("クリア完了")
else:
    print(f"クリア失敗: {response.status_code}")

all_questions = []

for round_num in range(1, ROUNDS + 1):
    print(f"\n{'='*60}")
    print(f"Round {round_num}/{ROUNDS}")
    print(f"{'='*60}")

    try:
        with open(PDF_PATH, 'rb') as pdf_file:
            files = {
                'source_file': (os.path.basename(PDF_PATH), pdf_file, 'application/pdf')
            }
            data = {
                'num_questions': QUESTIONS_PER_ROUND,
                'category': 'AI生成'
            }

            response = requests.post(
                f"{BASE_URL}/admin/auto_generate",
                files=files,
                data=data,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    generated_count = result.get('generated_count', 0)
                    print(f"生成成功: {generated_count}件")

                    # 承認待ちFAQ一覧を取得して最新の質問を表示
                    pending_response = requests.get(f"{BASE_URL}/admin/pending")
                    if pending_response.status_code == 200:
                        # HTMLレスポンスからJSONを取得する別のエンドポイントがないため、
                        # 生成されたcount分だけ記録
                        print(f"  (詳細はpending_qa.csvを確認)")
                        # 仮に質問をカウント
                        for i in range(generated_count):
                            all_questions.append(f"Round{round_num}_Q{i+1}")
                else:
                    print(f"失敗: {result.get('message', 'Unknown error')}")
            else:
                print(f"エラー: HTTP {response.status_code}")
                print(response.text[:500])

    except Exception as e:
        print(f"エラー: {str(e)}")

    if round_num < ROUNDS:
        print(f"次のラウンドまで5秒待機...")
        time.sleep(5)

# 結果サマリー
print(f"\n{'='*60}")
print("テスト完了")
print(f"{'='*60}")
print(f"総ラウンド数: {ROUNDS}")
print(f"想定質問数: {ROUNDS * QUESTIONS_PER_ROUND}")
print(f"\n本番環境のpending_qa.csvを直接確認してください。")
print(f"Railwayログで[DEBUG]メッセージから実際の質問内容と重複状況を確認できます。")
