import requests
import time
import os
import csv

BASE_URL = "https://faqsystem-production.up.railway.app"
ROUNDS = 10
QUESTIONS_PER_ROUND = 10
PDF_PATH = "reference_docs/第2章.pdf"
PENDING_CSV = "pending_qa.csv"

print("FAQ自動生成テスト開始（本番環境）")
print(f"URL: {BASE_URL}")
print(f"ラウンド数: {ROUNDS}")
print(f"1ラウンドあたりの質問数: {QUESTIONS_PER_ROUND}")
print("="*60)

# pending_qa.csvをクリア
with open(PENDING_CSV, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'question', 'answer', 'keywords', 'category', 'created_at', 'user_question', 'confirmation_request', 'comment'])

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
                    print(f"生成された質問数: {generated_count}")

                    # pending_qa.csvから最新の質問を取得
                    with open(PENDING_CSV, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        current_questions = [row['question'] for row in reader]

                    # 新しく追加された質問のみ表示
                    new_questions = current_questions[-generated_count:] if generated_count > 0 else []

                    print("\n生成された質問:")
                    for i, question in enumerate(new_questions, 1):
                        print(f"  {i}. {question}")
                        all_questions.append(question)
                else:
                    print(f"失敗: {result.get('message', 'Unknown error')}")
            else:
                print(f"エラー: HTTP {response.status_code}")
                print(response.text[:500])

    except Exception as e:
        print(f"エラー: {str(e)}")

    if round_num < ROUNDS:
        print("\n次のラウンドまで5秒待機...")
        time.sleep(5)

# 重複チェック
print(f"\n{'='*60}")
print("重複チェック")
print(f"{'='*60}")
print(f"総質問数: {len(all_questions)}")
print(f"ユニーク質問数: {len(set(all_questions))}")
print(f"重複数: {len(all_questions) - len(set(all_questions))}")

if len(all_questions) != len(set(all_questions)):
    print("\n重複質問:")
    seen = set()
    duplicates = []
    for q in all_questions:
        if q in seen:
            duplicates.append(q)
        seen.add(q)

    for dup in set(duplicates):
        count = all_questions.count(dup)
        print(f"  - {dup} ({count}回)")
else:
    print("\nOK: 重複なし")

print(f"\n{'='*60}")
print("全質問リスト")
print(f"{'='*60}")
for i, q in enumerate(all_questions, 1):
    print(f"{i}. {q}")
