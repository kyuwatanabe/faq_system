#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Claude APIのモック版テスト - 実際のAPIキーなしでQ&A改善をテスト
"""

import os
from faq_system import FAQSystem

def mock_claude_improvement(user_question, matched_question, matched_answer):
    """
    Claude APIの代わりにルールベースでQ&Aを改善するモック関数
    """

    # 簡単なルールベース改善
    if "入国許可証" in user_question:
        return {
            'question': "入国許可証（I-94）とは何ですか？",
            'answer': "入国許可証（I-94）は、外国人がアメリカに入国する際に発行される滞在許可証です。滞在可能な期限や滞在ステータスが記録されており、ビザとは別の重要な書類です。電子版はCBPのウェブサイトで確認できます。",
            'keywords': "入国許可証,I-94,滞在許可,CBP",
            'category': "入国手続き"
        }
    elif "滞在許可" in user_question:
        return {
            'question': "滞在許可とビザの違いは何ですか？",
            'answer': "ビザは入国のための許可証で、滞在許可（I-94）は実際にアメリカに滞在できる期間を示します。ビザの有効期限が切れても、I-94が有効であれば合法的に滞在できますが、一度出国すると有効なビザが必要になります。",
            'keywords': "滞在許可,ビザ,I-94,有効期限",
            'category': "滞在ステータス"
        }
    else:
        return {
            'question': f"改善版：{user_question}",
            'answer': f"【自動改善】{user_question}について、より詳細な回答を提供いたします。具体的な状況により異なる場合がありますので、詳細は専門家にご相談ください。",
            'keywords': "一般,改善版",
            'category': "その他"
        }

def test_mock_improvement():
    """モック改善機能をテスト"""
    faq_system = FAQSystem('faq_data-1.csv')

    # テスト用の質問
    test_questions = [
        "入国許可証って何？",
        "滞在許可って何？",
        "ビザの更新はどうするの？"
    ]

    print("=== モック Claude改善テスト ===")
    for question in test_questions:
        print(f"\n元の質問: {question}")

        # モック改善を実行
        improved = mock_claude_improvement(question, None, None)

        print(f"改善された質問: {improved['question']}")
        print(f"改善された回答: {improved['answer']}")

        # FAQに追加
        faq_system.add_faq(
            question=improved['question'],
            answer=improved['answer'],
            keywords=improved['keywords'],
            category=improved['category']
        )

        print("[OK] FAQに追加されました")

    # 保存
    faq_system.save_faq_data()
    print(f"\n[OK] {len(test_questions)}件の改善されたQ&AをFAQに追加しました")

if __name__ == "__main__":
    test_mock_improvement()