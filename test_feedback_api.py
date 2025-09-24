#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
フィードバックAPIのテストスクリプト
"""
import requests
import json

# テスト用のフィードバックデータ
feedback_data = {
    "satisfied": False,
    "user_question": "H-1Bビザの申請について教えて",
    "matched_question": "専門職ビザについて",
    "matched_answer": "専門職にはH-1Bビザが適しています。詳細は各ビザページをご確認いただくか担当者にお問い合わせください。"
}

print("=== フィードバックAPIテスト ===")
print(f"テストデータ: {json.dumps(feedback_data, ensure_ascii=False, indent=2)}")

try:
    # ローカルのFlaskアプリにPOSTリクエストを送信
    response = requests.post(
        "http://127.0.0.1:5000/feedback",
        json=feedback_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"\n=== レスポンス ===")
    print(f"ステータスコード: {response.status_code}")
    print(f"レスポンス内容: {response.json()}")

except requests.exceptions.RequestException as e:
    print(f"APIリクエストエラー: {e}")
except json.JSONDecodeError as e:
    print(f"JSONデコードエラー: {e}")
    print(f"生のレスポンス: {response.text}")