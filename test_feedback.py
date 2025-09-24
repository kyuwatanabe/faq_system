from faq_system import FAQSystem

# テスト用のスクリプト
faq = FAQSystem('faq_data-1.csv')

# 不満足なフィードバックをテスト
faq.save_unsatisfied_qa(
    user_question="テスト質問：H-1Bビザって何？",
    matched_question="専門職に必要なビザは何ですか？",
    matched_answer="専門職にはH-1Bビザが適しています。高度な専門知識を必要とする分野での専門職が対象で、I-797に準じた期間滞在でき、累積で最大6年まで可能です。"
)

print("テスト完了 - unsatisfied_qa.csvをチェックしてください")