from faq_system import FAQSystem

# PDFとテキストファイルの読み込みテスト
faq = FAQSystem('faq_data-1.csv')

print("=== 参考資料読み込みテスト ===")
reference_content = faq.load_reference_documents()

if reference_content:
    print(f"参考資料の長さ: {len(reference_content)}文字")
    print("\n--- 参考資料の先頭200文字 ---")
    print(reference_content[:200])
    print("...")

    # PDFが含まれているか確認
    if "第2章.pdf" in reference_content:
        print("\n✅ PDFファイルが正常に読み込まれました")
    else:
        print("\n❌ PDFファイルの読み込みに失敗")

else:
    print("❌ 参考資料が読み込めませんでした")