import csv
import difflib
from typing import List, Dict, Tuple


class FAQSystem:
    def __init__(self, csv_file: str):
        self.faq_data = []
        self.pending_qa = []
        self.csv_file = csv_file
        self.pending_file = 'pending_qa.csv'
        self.load_faq_data(csv_file)
        self.load_pending_qa()

    def load_faq_data(self, csv_file: str) -> None:
        """CSVファイルからFAQデータを読み込む"""
        # 既存データをクリア
        self.faq_data.clear()
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    self.faq_data.append({
                        'question': row.get('question', '').strip(),
                        'answer': row.get('answer', '').strip(),
                        'keywords': row.get('keywords', '').strip(),
                        'category': row.get('category', '一般').strip()
                    })
            print(f"FAQデータを{len(self.faq_data)}件読み込みました")
        except FileNotFoundError:
            print(f"エラー: {csv_file} が見つかりません")
        except Exception as e:
            print(f"エラー: {e}")

    def load_pending_qa(self) -> None:
        """承認待ちQ&Aデータを読み込む"""
        self.pending_qa.clear()
        try:
            with open(self.pending_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    self.pending_qa.append({
                        'id': row.get('id', ''),
                        'question': row.get('question', '').strip(),
                        'answer': row.get('answer', '').strip(),
                        'keywords': row.get('keywords', '').strip(),
                        'category': row.get('category', '一般').strip(),
                        'created_at': row.get('created_at', ''),
                        'user_question': row.get('user_question', '').strip()
                    })
            print(f"承認待ちQ&Aを{len(self.pending_qa)}件読み込みました")
        except FileNotFoundError:
            print("承認待ちQ&Aファイルが存在しません。新規作成します。")
            self.save_pending_qa()
        except Exception as e:
            print(f"承認待ちQ&A読み込みエラー: {e}")

    def save_pending_qa(self) -> None:
        """承認待ちQ&Aをファイルに保存"""
        try:
            with open(self.pending_file, 'w', encoding='utf-8-sig', newline='') as file:
                if self.pending_qa:
                    fieldnames = ['id', 'question', 'answer', 'keywords', 'category', 'created_at', 'user_question']
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.pending_qa)
                else:
                    # 空ファイルでもヘッダーは書く
                    writer = csv.writer(file)
                    writer.writerow(['id', 'question', 'answer', 'keywords', 'category', 'created_at', 'user_question'])
        except Exception as e:
            print(f"承認待ちQ&A保存エラー: {e}")

    def add_pending_qa(self, question: str, answer: str, keywords: str = '', category: str = '一般', user_question: str = '') -> str:
        """承認待ちQ&Aを追加"""
        import datetime
        import uuid

        qa_id = str(uuid.uuid4())[:8]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.pending_qa.append({
            'id': qa_id,
            'question': question,
            'answer': answer,
            'keywords': keywords,
            'category': category,
            'created_at': timestamp,
            'user_question': user_question
        })

        self.save_pending_qa()
        return qa_id

    def approve_pending_qa(self, qa_id: str) -> bool:
        """承認待ちQ&Aを承認してFAQに追加"""
        for i, pending in enumerate(self.pending_qa):
            if pending['id'] == qa_id:
                # FAQに追加
                self.add_faq(
                    question=pending['question'],
                    answer=pending['answer'],
                    keywords=pending['keywords'],
                    category=pending['category']
                )

                # 承認待ちから削除
                del self.pending_qa[i]
                self.save_pending_qa()
                self.save_faq_data()

                print(f"[承認] Q&A「{pending['question']}」を承認しました")
                return True
        return False

    def reject_pending_qa(self, qa_id: str) -> bool:
        """承認待ちQ&Aを却下"""
        for i, pending in enumerate(self.pending_qa):
            if pending['id'] == qa_id:
                rejected_question = pending['question']
                del self.pending_qa[i]
                self.save_pending_qa()
                print(f"[却下] Q&A「{rejected_question}」を却下しました")
                return True
        return False

    def edit_pending_qa(self, qa_id: str, question: str = None, answer: str = None, keywords: str = None, category: str = None) -> bool:
        """承認待ちQ&Aを編集"""
        for pending in self.pending_qa:
            if pending['id'] == qa_id:
                if question:
                    pending['question'] = question
                if answer:
                    pending['answer'] = answer
                if keywords is not None:
                    pending['keywords'] = keywords
                if category:
                    pending['category'] = category

                self.save_pending_qa()
                print(f"[編集] 承認待ちQ&A「{qa_id}」を編集しました")
                return True
        return False

    def get_keyword_score(self, user_question: str, faq_question: str, faq_keywords: str = '') -> float:
        """キーワードベースのスコアを計算"""
        # 料金関連キーワード
        money_keywords = ['料金', '費用', 'お金', '金額', '価格', '値段', 'コスト', '費用']
        # 時間関連キーワード
        time_keywords = ['時間', '期間', '日数', 'いつ', '何日', '何週間', '何か月']
        # 面接関連キーワード
        interview_keywords = ['面接', '面談', 'インタビュー']
        # 書類関連キーワード
        document_keywords = ['書類', '必要', '資料', 'ドキュメント', '準備']
        # サービス関連キーワード
        service_keywords = ['サービス', '範囲', 'サポート', 'どこまで']

        user_lower = user_question.lower()
        faq_lower = faq_question.lower()
        faq_keywords_lower = faq_keywords.lower()

        # キーワードマッチのボーナススコア
        score = 0.0

        # CSVのキーワードフィールドを活用
        if faq_keywords:
            # セミコロン区切りのキーワードを分割
            csv_keywords = [kw.strip().lower() for kw in faq_keywords.split(';')]
            for keyword in csv_keywords:
                if keyword and keyword in user_lower:
                    score += 0.8  # CSVのキーワード完全マッチに高いスコア

        # 既存のキーワードマッチング（従来のロジック）
        # 料金関連
        if any(keyword in user_lower for keyword in money_keywords):
            if any(keyword in faq_lower for keyword in money_keywords) or any(keyword in faq_keywords_lower for keyword in money_keywords):
                score += 0.3
            elif any(keyword in faq_lower for keyword in time_keywords):
                score -= 0.2

        # 時間関連
        if any(keyword in user_lower for keyword in time_keywords):
            if any(keyword in faq_lower for keyword in time_keywords) or any(keyword in faq_keywords_lower for keyword in time_keywords):
                score += 0.3
            elif any(keyword in faq_lower for keyword in money_keywords):
                score -= 0.2

        # その他のキーワードマッチ
        if any(keyword in user_lower for keyword in interview_keywords):
            if any(keyword in faq_lower for keyword in interview_keywords) or any(keyword in faq_keywords_lower for keyword in interview_keywords):
                score += 0.3

        if any(keyword in user_lower for keyword in document_keywords):
            if any(keyword in faq_lower for keyword in document_keywords) or any(keyword in faq_keywords_lower for keyword in document_keywords):
                score += 0.2

        if any(keyword in user_lower for keyword in service_keywords):
            if any(keyword in faq_lower for keyword in service_keywords) or any(keyword in faq_keywords_lower for keyword in service_keywords):
                score += 0.2

        return score

    def calculate_similarity(self, question1: str, question2: str) -> float:
        """2つの質問の類似度を計算（0.0〜1.0）"""
        return difflib.SequenceMatcher(
            None,
            question1.lower(),
            question2.lower()
        ).ratio()

    def search_faq(self, user_question: str, threshold: float = 0.3) -> List[Dict]:
        """ユーザーの質問に対して最適なFAQを検索"""
        if not user_question.strip():
            return []

        results = []

        for faq in self.faq_data:
            # 文字列の類似度を計算
            string_similarity = difflib.SequenceMatcher(
                None,
                user_question.lower(),
                faq['question'].lower()
            ).ratio()

            # キーワードスコアを計算
            keyword_score = self.get_keyword_score(user_question, faq['question'], faq['keywords'])

            # 総合スコアを計算（文字列類似度 + キーワードスコア）
            total_score = string_similarity + keyword_score

            # 閾値以上のスコアがあれば結果に追加
            if total_score >= threshold:
                results.append({
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'category': faq['category'],
                    'similarity': total_score,
                    'string_similarity': string_similarity,
                    'keyword_score': keyword_score
                })

        # 総合スコアの高い順にソート
        results.sort(key=lambda x: x['similarity'], reverse=True)

        return results

    def get_best_answer(self, user_question: str) -> tuple:
        """最も適切な回答を取得"""
        results = self.search_faq(user_question)

        if not results:
            return ("申し訳ございませんが、該当する質問が見つかりませんでした。より具体的に質問していただくか、お電話でお問い合わせください。", False)

        best_match = results[0]

        # 類似度が0.7未満の場合は確認を求める
        if best_match['similarity'] < 0.7:
            return (best_match, True)  # 確認が必要
        else:
            return (best_match['answer'], False)  # 確認不要

    def format_answer(self, match: dict) -> str:
        """回答をフォーマット"""
        return match['answer']

    def save_faq_data(self) -> None:
        """FAQデータをCSVファイルに保存"""
        try:
            with open('faq_data-1.csv', 'w', encoding='utf-8-sig', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['question', 'answer', 'keywords', 'category'])
                writer.writeheader()
                for faq in self.faq_data:
                    writer.writerow({
                        'question': faq['question'],
                        'answer': faq['answer'],
                        'keywords': faq.get('keywords', ''),
                        'category': faq.get('category', '一般')
                    })
            print("FAQデータを保存しました。")
        except Exception as e:
            print(f"保存エラー: {e}")

    def add_faq(self, question: str, answer: str, keywords: str = '', category: str = '一般') -> None:
        """新しいFAQを追加"""
        self.faq_data.append({
            'question': question.strip(),
            'answer': answer.strip(),
            'keywords': keywords.strip(),
            'category': category.strip()
        })

    def edit_faq(self, index: int, question: str = None, answer: str = None) -> bool:
        """FAQを編集"""
        if 0 <= index < len(self.faq_data):
            if question:
                self.faq_data[index]['question'] = question.strip()
            if answer:
                self.faq_data[index]['answer'] = answer.strip()
            return True
        return False

    def delete_faq(self, index: int) -> bool:
        """FAQを削除"""
        if 0 <= index < len(self.faq_data):
            self.faq_data.pop(index)
            return True
        return False

    def show_all_faqs(self) -> None:
        """すべてのFAQを表示"""
        print("\n=== 現在のFAQデータ ===")
        for i, faq in enumerate(self.faq_data):
            print(f"\n{i+1}. 質問: {faq['question']}")
            print(f"   回答: {faq['answer']}")
        print(f"\n合計: {len(self.faq_data)}件")

    def save_unsatisfied_qa(self, user_question: str, matched_question: str, matched_answer: str, timestamp: str = None) -> None:
        """不満足なQ&Aを別ファイルに保存"""
        import datetime
        import os

        if not timestamp:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 現在のスクリプトと同じディレクトリに保存
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, 'unsatisfied_qa.csv')

        try:
            # ファイルが存在するかチェック
            file_exists = os.path.exists(csv_path)

            with open(csv_path, 'a', encoding='utf-8-sig', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['timestamp', 'user_question', 'matched_question', 'matched_answer'])

                if not file_exists:
                    writer.writeheader()

                writer.writerow({
                    'timestamp': timestamp,
                    'user_question': user_question,
                    'matched_question': matched_question,
                    'matched_answer': matched_answer
                })

            print("不満足なQ&Aを記録しました。")
        except Exception as e:
            print(f"記録エラー: {e}")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDFからテキストを抽出"""
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            print("PyPDF2がインストールされていません。pip install PyPDF2を実行してください")
            return ""
        except Exception as e:
            print(f"PDF読み込みエラー {pdf_path}: {e}")
            return ""

    def load_reference_documents(self) -> str:
        """参考資料を読み込む（PDF、TXT対応）"""
        try:
            import os
            reference_content = ""

            # 参考資料ディレクトリから文書を読み込み
            reference_dir = os.path.join(os.path.dirname(__file__), 'reference_docs')
            if os.path.exists(reference_dir):
                # ファイルを名前でソート（優先順位を付けたい場合）
                files = sorted(os.listdir(reference_dir))

                for filename in files:
                    file_path = os.path.join(reference_dir, filename)

                    if filename.endswith('.txt'):
                        # テキストファイル読み込み
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                reference_content += f"\n\n=== {filename} ===\n"
                                reference_content += content
                        except UnicodeDecodeError:
                            # UTF-8で読めない場合はcp932（Shift_JIS）で試す
                            with open(file_path, 'r', encoding='cp932') as f:
                                content = f.read()
                                reference_content += f"\n\n=== {filename} ===\n"
                                reference_content += content

                    elif filename.endswith('.pdf'):
                        # PDFファイル読み込み
                        pdf_content = self.extract_text_from_pdf(file_path)
                        if pdf_content:
                            reference_content += f"\n\n=== {filename} ===\n"
                            reference_content += pdf_content

                    elif filename.endswith(('.md', '.markdown')):
                        # Markdownファイル読み込み
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                reference_content += f"\n\n=== {filename} ===\n"
                                reference_content += content
                        except Exception as e:
                            print(f"Markdown読み込みエラー {filename}: {e}")

            # 参考資料が長すぎる場合は制限（Claude APIのトークン制限対応）
            if len(reference_content) > 10000:  # 約10,000文字で制限
                reference_content = reference_content[:10000] + "\n\n[... 参考資料が長いため省略 ...]"

            return reference_content
        except Exception as e:
            print(f"参考資料読み込みエラー: {e}")
            return ""

    def generate_improved_qa_with_claude(self, user_question: str, current_answer: str, use_references: bool = True) -> dict:
        """ClaudeでQ&Aを改善生成"""
        try:
            import requests
            import json
            import os

            # Claude API設定（環境変数から取得）
            api_key = os.getenv('CLAUDE_API_KEY')
            if not api_key:
                print("CLAUDE_API_KEY未設定。モック改善機能を使用します...")
                return self._mock_claude_improvement(user_question, current_answer)

            # 参考資料を取得
            reference_docs = ""
            if use_references:
                reference_docs = self.load_reference_documents()

            # 既存のFAQコンテキストを構築
            existing_context = "\n".join([
                f"Q: {faq['question']}\nA: {faq['answer']}"
                for faq in self.faq_data[:10]  # 最初の10件を参考として使用
            ])

            # プロンプト作成
            prompt = f"""
あなたはアメリカビザ専門のFAQシステムの改善を担当するエキスパートです。

【状況】
ユーザーが以下の質問をしましたが、システムの回答に満足していませんでした。
より正確で役立つ回答を作成する必要があります。

【ユーザーの実際の質問】
{user_question}

【システムが提供した回答（不満足）】
{current_answer}

【既存のFAQコンテキスト（参考）】
{existing_context}

{f'''【参考資料】
{reference_docs}''' if reference_docs else ""}

【改善要件】
1. ユーザーの質問の意図を正確に理解し、それに応える内容にする
2. アメリカビザに関する正確で最新の情報を含める
3. 実用的で具体的なアドバイスを含める
4. 日本人向けに分かりやすい日本語で説明する
5. 専門用語は適切に説明を加える
6. 関連する手続きや注意点も含める

【出力形式】
以下のJSON形式で回答してください：
{{
  "question": "改善された質問文（ユーザーの意図をより正確に表現）",
  "answer": "改善された詳細な回答文（具体的で実用的な内容）",
  "keywords": "関連キーワード（セミコロン区切り）",
  "category": "適切なカテゴリ名"
}}
"""

            headers = {
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            }

            data = {
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 1000,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            }

            # JSONをダンプして確実にエスケープする
            import json
            json_data = json.dumps(data, ensure_ascii=False)

            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                data=json_data.encode('utf-8'),
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']

                # JSON部分を抽出
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    qa_data = json.loads(json_match.group())
                    return qa_data
                else:
                    print("Claude の回答からJSONを抽出できませんでした")
                    return None
            else:
                print(f"[DEBUG] Claude API エラー - ステータス: {response.status_code}")
                print(f"[DEBUG] エラーレスポンス: {response.text}")
                print(f"[DEBUG] APIが失敗、モック機能に切り替えます")
                return self._mock_claude_improvement(user_question, current_answer)

        except Exception as e:
            print(f"[DEBUG] Claude API 呼び出しエラー詳細: {e}")
            print(f"[DEBUG] 例外が発生、モック機能に切り替えます")
            return self._mock_claude_improvement(user_question, current_answer)

    def auto_improve_qa(self, user_question: str, matched_question: str, matched_answer: str) -> bool:
        """不満足なQ&Aを自動改善して承認待ちキューに追加"""
        print("Claude でQ&Aを自動改善中...")

        improved_qa = self.generate_improved_qa_with_claude(user_question, matched_answer)

        if improved_qa:
            # 改善されたQ&Aを承認待ちキューに追加
            qa_id = self.add_pending_qa(
                question=improved_qa['question'],
                answer=improved_qa['answer'],
                keywords=improved_qa.get('keywords', ''),
                category=improved_qa.get('category', 'AI生成'),
                user_question=user_question
            )

            print(f"[追加] 新しいQ&Aを承認待ちキューに追加しました (ID: {qa_id}):")
            print(f"質問: {improved_qa['question']}")
            print(f"回答: {improved_qa['answer'][:100]}...")

            return True
        else:
            print("[失敗] Q&Aの改善に失敗しました")
            return False

    def _mock_claude_improvement(self, user_question: str, current_answer: str) -> dict:
        """Claude APIの代わりにルールベースでQ&Aを改善するモック関数"""

        # 簡単なルールベース改善
        if "入国許可証" in user_question:
            return {
                'question': "入国許可証（I-94）とは何ですか？",
                'answer': "入国許可証（I-94）は、外国人がアメリカに入国する際に発行される滞在許可証です。滞在可能な期限や滞在ステータスが記録されており、ビザとは別の重要な書類です。電子版はCBPのウェブサイトで確認できます。",
                'keywords': "入国許可証;I-94;滞在許可;CBP",
                'category': "入国手続き"
            }
        elif "滞在許可" in user_question:
            return {
                'question': "滞在許可とビザの違いは何ですか？",
                'answer': "ビザは入国のための許可証で、滞在許可（I-94）は実際にアメリカに滞在できる期間を示します。ビザの有効期限が切れても、I-94が有効であれば合法的に滞在できますが、一度出国すると有効なビザが必要になります。",
                'keywords': "滞在許可;ビザ;I-94;有効期限",
                'category': "滞在ステータス"
            }
        elif "h-1b" in user_question.lower() or "専門職" in user_question:
            return {
                'question': f"H-1Bビザに関する質問：{user_question}",
                'answer': f"H-1Bビザについて詳しくお答えします。H-1Bビザは専門職従事者向けのビザで、学士号以上の学位またはそれに相当する実務経験が必要です。年間発給数に上限があり、抽選制となっています。申請には雇用主のスポンサーシップが必要で、最長6年間の滞在が可能です。",
                'keywords': "H-1B;専門職;ビザ;抽選;雇用主",
                'category': "就労ビザ"
            }
        elif "商用" in user_question and ("無給" in user_question or "給与" in user_question):
            return {
                'question': "無給での活動は商用ビザで可能ですか？",
                'answer': "はい、可能です。商用ビザ（B-1）は無給での商取引活動を対象としています。契約交渉、会議参加、研修参加、市場調査などは給与を受け取らない限り商用活動に該当します。ただし、現地での就労行為（現地スタッフが行うべき作業）は禁止されており、判断が難しい場合は事前に確認することをお勧めします。",
                'keywords': "商用;B-1;無給;契約交渉;会議;研修;市場調査",
                'category': "商用ビザ"
            }
        else:
            return {
                'question': f"改善版：{user_question}",
                'answer': f"【自動改善】{user_question}について、より詳細な回答を提供いたします。ビザ申請は複雑な手続きのため、具体的な状況により異なる場合があります。詳細な相談が必要な場合は、専門家にご相談いただくか、お電話でお問い合わせください。",
                'keywords': "一般;改善版;相談",
                'category': "その他"
            }


def admin_mode(faq):
    """管理者モード"""
    while True:
        print("\n=== FAQ管理モード ===")
        print("1. 全FAQ表示")
        print("2. FAQ追加")
        print("3. FAQ編集")
        print("4. FAQ削除")
        print("5. 保存")
        print("6. ユーザーモードに戻る")

        choice = input("\n選択 (1-6): ").strip()

        if choice == '1':
            faq.show_all_faqs()
        elif choice == '2':
            question = input("\n質問を入力: ")
            answer = input("回答を入力: ")
            if question.strip() and answer.strip():
                faq.add_faq(question, answer)
                print("FAQを追加しました。")
            else:
                print("質問と回答の両方を入力してください。")
        elif choice == '3':
            faq.show_all_faqs()
            try:
                index = int(input("\n編集するFAQ番号: ")) - 1
                if 0 <= index < len(faq.faq_data):
                    current_faq = faq.faq_data[index]
                    print(f"\n現在の質問: {current_faq['question']}")
                    print(f"現在の回答: {current_faq['answer']}")

                    new_question = input("\n新しい質問 (変更しない場合は空欄): ")
                    new_answer = input("新しい回答 (変更しない場合は空欄): ")

                    if faq.edit_faq(index, new_question if new_question else None, new_answer if new_answer else None):
                        print("FAQを更新しました。")
                else:
                    print("無効な番号です。")
            except ValueError:
                print("数字を入力してください。")
        elif choice == '4':
            faq.show_all_faqs()
            try:
                index = int(input("\n削除するFAQ番号: ")) - 1
                if faq.delete_faq(index):
                    print("FAQを削除しました。")
                else:
                    print("無効な番号です。")
            except ValueError:
                print("数字を入力してください。")
        elif choice == '5':
            faq.save_faq_data()
        elif choice == '6':
            break
        else:
            print("1-6の数字を入力してください。")

def main():
    # FAQシステムを初期化
    faq = FAQSystem('faq_data.csv')

    print("=== ビザ申請代行 FAQ自動回答システム ===")
    print("質問を入力してください（'quit'で終了、'admin'で管理モード）")
    print("-" * 50)

    while True:
        user_input = input("\n質問: ")

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("システムを終了します。")
            break
        elif user_input.lower() == 'admin':
            admin_mode(faq)
            continue

        if not user_input.strip():
            print("質問を入力してください。")
            continue

        # 回答を検索
        result, needs_confirmation = faq.get_best_answer(user_input)

        if needs_confirmation:
            # 確認が必要な場合
            print(f"\nご質問は「{result['question']}」ということでしょうか？")
            print("1. はい")
            print("2. いいえ")
            print("3. 管理モード（この回答を編集）")

            while True:
                choice = input("\n選択 (1/2/3): ").strip()

                if choice == '1':
                    # はいの場合、回答を表示
                    answer = faq.format_answer(result)
                    print(f"\n{answer}")
                    break
                elif choice == '2':
                    # いいえの場合、再質問を促す
                    print("\n申し訳ございません。別の言い方で質問していただけますでしょうか。")
                    break
                elif choice == '3':
                    # 管理モードに入る
                    print(f"\n現在の質問: {result['question']}")
                    print(f"現在の回答: {result['answer']}")

                    # 該当するFAQのインデックスを見つける
                    for i, faq_item in enumerate(faq.faq_data):
                        if faq_item['question'] == result['question']:
                            new_question = input("\n新しい質問 (変更しない場合は空欄): ")
                            new_answer = input("新しい回答 (変更しない場合は空欄): ")

                            if faq.edit_faq(i, new_question if new_question else None, new_answer if new_answer else None):
                                print("FAQを更新しました。")
                                faq.save_faq_data()
                            break
                    break
                else:
                    print("1、2、または 3 を入力してください。")
        else:
            # 確認不要の場合、直接回答を表示
            print(f"\n{result}")

        print("-" * 50)

def find_similar_faqs(faq_system, question: str, threshold: float = 0.6, max_results: int = 5) -> list:
    """既存のFAQから類似する質問を検出"""
    similar_faqs = []

    for faq in faq_system.faq_data:
        # 文字列類似度とキーワードスコアを組み合わせて計算
        similarity = faq_system.calculate_similarity(question, faq['question'])
        keyword_score = faq_system.get_keyword_score(question, faq['question'], faq.get('keywords', ''))

        # 総合スコア（類似度70%、キーワード30%の重み付け）
        total_score = similarity * 0.7 + keyword_score * 0.3

        if total_score >= threshold:
            similar_faqs.append({
                'question': faq['question'],
                'answer': faq['answer'],
                'keywords': faq.get('keywords', ''),
                'category': faq.get('category', ''),
                'similarity_score': round(total_score, 3)
            })

    # スコア順でソートして上位結果を返す
    similar_faqs.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similar_faqs[:max_results]


if __name__ == "__main__":
    main()