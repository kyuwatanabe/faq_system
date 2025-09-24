from faq_system import FAQSystem

# FAQシステムをテスト
faq = FAQSystem('faq_data.csv')

# テスト質問
test_questions = [
    "料金はいくらですか？",
    "料金について教えて",
    "費用はいくらかかりますか？",
    "どのくらいお金がかかる？",
    "面接は必要ですか？",
    "何日かかりますか？"
]

print("=== FAQシステムのテスト ===\n")

for question in test_questions:
    print(f"質問: {question}")
    results = faq.search_faq(question)
    if results:
        top_result = results[0]
        print(f"総合スコア: {top_result['similarity']:.3f} (文字列: {top_result['string_similarity']:.3f}, キーワード: {top_result['keyword_score']:.3f})")
        print(f"マッチした質問: {top_result['question']}")

    result, needs_confirmation = faq.get_best_answer(question)

    if needs_confirmation:
        print(f"確認必要: ご質問は「{result['question']}」ということでしょうか？")
        print("→ Yes/No選択が必要")
    else:
        print(f"回答: {result}")

    print("\n" + "-" * 50)