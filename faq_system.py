import csv
import difflib
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


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
                        'user_question': row.get('user_question', '').strip(),
                        'confirmation_request': row.get('confirmation_request', '0').strip(),
                        'comment': row.get('comment', '').strip()
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
                    fieldnames = ['id', 'question', 'answer', 'keywords', 'category', 'created_at', 'user_question', 'confirmation_request', 'comment']
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.pending_qa)
                else:
                    # 空ファイルでもヘッダーは書く
                    writer = csv.writer(file)
                    writer.writerow(['id', 'question', 'answer', 'keywords', 'category', 'created_at', 'user_question', 'confirmation_request'])
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
            'user_question': user_question,
            'confirmation_request': '0'
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

    def toggle_confirmation_request(self, qa_id: str) -> bool:
        """承認待ちQ&Aの確認依頼フラグを切り替え"""
        for pending in self.pending_qa:
            if pending['id'] == qa_id:
                # 確認依頼フラグを切り替え（0/1のトグル）
                current_value = pending.get('confirmation_request', '0')
                pending['confirmation_request'] = '0' if current_value == '1' else '1'

                self.save_pending_qa()
                status = '依頼中' if pending['confirmation_request'] == '1' else '解除'
                print(f"[確認依頼] 承認待ちFAQ「{qa_id}」の確認依頼を{status}にしました")
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

    def edit_faq(self, index: int, question: str = None, answer: str = None, category: str = None) -> bool:
        """FAQを編集"""
        if 0 <= index < len(self.faq_data):
            if question:
                self.faq_data[index]['question'] = question.strip()
            if answer:
                self.faq_data[index]['answer'] = answer.strip()
            if category is not None:
                self.faq_data[index]['category'] = category.strip() if category.strip() else '一般'
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

    def _load_generation_history(self) -> list:
        """FAQ生成履歴を読み込む"""
        history_file = 'faq_generation_history.csv'
        history = []
        try:
            with open(history_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    history.append({
                        'question': row.get('question', '').strip(),
                        'answer': row.get('answer', '').strip(),
                        'timestamp': row.get('timestamp', '').strip()
                    })
            print(f"[DEBUG] FAQ生成履歴を{len(history)}件読み込みました")
        except FileNotFoundError:
            print("[DEBUG] FAQ生成履歴ファイルが存在しません（初回生成）")
        except Exception as e:
            print(f"[DEBUG] FAQ生成履歴読み込みエラー: {e}")
        return history

    def _save_to_generation_history(self, faqs: list) -> None:
        """生成したFAQを履歴に保存"""
        import datetime
        import os

        history_file = 'faq_generation_history.csv'
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # ファイルが存在するかチェック
            file_exists = os.path.exists(history_file)

            with open(history_file, 'a', encoding='utf-8-sig', newline='') as file:
                fieldnames = ['timestamp', 'question', 'answer']
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                for faq in faqs:
                    writer.writerow({
                        'timestamp': timestamp,
                        'question': faq.get('question', ''),
                        'answer': faq.get('answer', '')
                    })

            print(f"[DEBUG] {len(faqs)}件のFAQを生成履歴に保存しました")
        except Exception as e:
            print(f"[DEBUG] FAQ生成履歴保存エラー: {e}")

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
                print(f"[DEBUG] Claude API成功 - ステータス: 200")
                content = result['content'][0]['text']
                print(f"[DEBUG] Claude レスポンス内容（最初の200文字）: {content[:200]}...")

                # JSON部分を抽出
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    # 改行文字を適切にエスケープ
                    json_str = json_match.group()
                    # 文字列内の改行をエスケープ（JSONパースエラーを防ぐ）
                    # まず正規表現で文字列値内の改行を検出して置換
                    json_str = re.sub(r'("(?:[^"\\]|\\.)*?")', lambda m: m.group(1).replace('\n', '\\n').replace('\r', '\\r'), json_str)

                    try:
                        qa_data = json.loads(json_str)
                        print(f"[DEBUG] JSONデータ抽出成功: {qa_data}")
                        return qa_data
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSONパースエラー: {e}")
                        print(f"[DEBUG] 問題のJSON: {json_str[:500]}...")
                        return self._mock_claude_improvement(user_question, current_answer)
                else:
                    print(f"[DEBUG] Claude の回答からJSONを抽出できませんでした。モック機能に切り替えます")
                    return self._mock_claude_improvement(user_question, current_answer)
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

    def generate_faqs_from_document(self, pdf_path: str, num_questions: int = 3, category: str = "AI生成") -> list:
        """PDFドキュメントからFAQを自動生成"""
        try:
            import requests
            import json
            import os

            # Claude API設定
            api_key = os.getenv('CLAUDE_API_KEY')
            if not api_key:
                print("CLAUDE_API_KEY未設定。モック生成機能を使用します...")
                return self._mock_faq_generation(num_questions, category)

            # PDFからテキストを抽出
            pdf_content = self.extract_text_from_pdf(pdf_path)
            if not pdf_content:
                print(f"PDFの読み込みに失敗: {pdf_path}")
                return []

            # 既存のFAQと承認待ちQ&Aの両方をチェック（重複を避けるため）
            existing_questions = [faq['question'] for faq in self.faq_data]

            # 承認待ちQ&Aも読み込んで追加
            self.load_pending_qa()
            pending_questions = [item['question'] for item in self.pending_qa if 'question' in item]

            # 過去に生成したFAQの履歴も読み込む
            generation_history = self._load_generation_history()
            history_questions = [item['question'] for item in generation_history if 'question' in item]

            # 既存、承認待ち、履歴を統合
            all_existing_questions = existing_questions + pending_questions + history_questions

            # 重複を除去して番号付きリストを作成
            unique_questions = []
            seen = set()
            for q in all_existing_questions:
                if q not in seen:
                    unique_questions.append(q)
                    seen.add(q)

            if unique_questions:
                existing_context = "以下の質問は既に存在するため、これらと同一または非常に類似した質問は生成しないでください：\n\n"
                existing_context += "\n".join([f"{i+1}. {q}" for i, q in enumerate(unique_questions[:100])])
            else:
                existing_context = "既存の質問はありません。"

            print(f"[DEBUG] 重複チェック対象 - 既存FAQ: {len(existing_questions)}件, 承認待ち: {len(pending_questions)}件, 履歴: {len(history_questions)}件")
            print(f"[DEBUG] ユニークな既存質問: {len(unique_questions)}件")

            # プロンプト作成
            prompt = f"""
あなたはアメリカビザ専門のFAQシステムのコンテンツ生成エキスパートです。

【タスク】
以下のPDFドキュメントから、{num_questions}個の有用なFAQ（質問と回答のペア）を生成してください。

【ソースドキュメント】
{pdf_content[:8000]}  # トークン制限を考慮

{existing_context}

【生成要件】
1. **最重要**: PDFドキュメントに明示的に記載されている内容のみからFAQを生成すること
2. PDFに記載されていない一般知識や推測による内容は絶対に含めないこと
3. **最重要**: 上記の既存質問リストを必ず確認し、それらと同一または酷似する質問は絶対に生成しないこと
4. 既存質問と完全に異なるトピックや、異なる角度・視点からの質問を生成すること
5. 実用的で具体的な質問を作成する
6. 日本人がよく聞きそうな質問にする
7. 回答は正確で詳細、かつ分かりやすい日本語で
8. 専門用語には適切な説明を加える
9. PDFに十分な情報がない場合は、生成する数を減らしても構わない

【重要な注意事項】
- PDFドキュメントに記載されている事実のみを使用してください
- 一般的なビザ知識や外部情報を追加しないでください
- 不明な点や記載がない内容については、FAQを生成しないでください

【出力形式】
以下のJSON配列形式でFAQを出力してください（最大{num_questions}個）：

**重要なJSON記述ルール**:
1. JSONの値内では改行文字を使用せず、すべて1行で記述してください
2. 強調のための引用符（"入国"、"滞在"など）は使用せず、通常の文として記述してください
3. 長い回答も改行せずにスペースで区切ってください

[
  {{
    "question": "具体的な質問文",
    "answer": "詳細で実用的な回答文（改行や引用符を使わず1行で記述）",
    "keywords": "関連キーワード1;関連キーワード2;関連キーワード3",
    "category": "{category}"
  }},
  ...
]

JSON形式のみを出力し、説明文は不要です。
"""

            headers = {
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            }

            data = {
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 4000,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            }

            json_data = json.dumps(data, ensure_ascii=False)

            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                data=json_data.encode('utf-8'),
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                print(f"[DEBUG] Claude FAQ生成成功")
                print(f"[DEBUG] Claude応答の最初の500文字: {content[:500]}")

                # JSON部分を抽出
                import re
                # JSONブロックを探す（```json ... ``` の形式も考慮）
                json_match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
                if not json_match:
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                    else:
                        json_str = None
                else:
                    json_str = json_match.group(1)

                if json_str:
                    print(f"[DEBUG] 抽出したJSON（最初の300文字）: {json_str[:300]}")
                    try:
                        # JSON文字列のクリーニング
                        import unicodedata

                        # ステップ1: 制御文字を除去（JSON構造に必要な文字は保持）
                        cleaned_json = ''.join(
                            char if char in '{}[]":,\n\t ' or not unicodedata.category(char).startswith('C')
                            else ' '
                            for char in json_str
                        )

                        # ステップ2: 最もシンプルなアプローチ - json.decoder.JSONDecodeError を処理
                        # まず通常のJSONパースを試み、失敗したら値内のクォートを置換
                        print(f"[DEBUG] クリーニング後のJSON（最初の300文字）: {cleaned_json[:300]}")

                        try:
                            faqs = json.loads(cleaned_json)
                        except json.JSONDecodeError as json_err:
                            print(f"[DEBUG] 初回JSONパース失敗: {json_err}")
                            print(f"[DEBUG] JSON値内のクォートを修正して再試行...")

                            # 値内のダブルクォートを全てシングルクォートに置換
                            # 簡易的な方法: JSON構造外のクォートは少ないと仮定
                            # ": " の後から次の " までの間にある " を ' に置換
                            import re

                            def replace_inner_quotes(text):
                                """JSON値内のダブルクォートをシングルクォートに置換"""
                                result = []
                                i = 0
                                while i < len(text):
                                    # ": " パターンを探す
                                    if i < len(text) - 3 and text[i:i+3] == '": ':
                                        result.append(text[i:i+3])
                                        i += 3
                                        # 次のダブルクォートまでの値部分を処理
                                        if i < len(text) and text[i] == '"':
                                            result.append('"')
                                            i += 1
                                            value_chars = []
                                            while i < len(text):
                                                if text[i] == '"' and (i + 1 >= len(text) or text[i+1] in ',\n}]'):
                                                    # 値の終了
                                                    result.append(''.join(value_chars).replace('"', "'"))
                                                    result.append('"')
                                                    i += 1
                                                    break
                                                else:
                                                    value_chars.append(text[i])
                                                    i += 1
                                    else:
                                        result.append(text[i])
                                        i += 1
                                return ''.join(result)

                            cleaned_json = replace_inner_quotes(cleaned_json)
                            print(f"[DEBUG] クォート修正後のJSON（最初の300文字）: {cleaned_json[:300]}")
                            faqs = json.loads(cleaned_json)
                        print(f"[DEBUG] {len(faqs)}件のFAQを生成しました")
                        # 生成したFAQを履歴に保存
                        self._save_to_generation_history(faqs)
                        return faqs
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSONパースエラー: {e}")
                        print(f"[DEBUG] パース失敗したJSON（最初の500文字）: {json_str[:500]}")
                        return self._mock_faq_generation(num_questions, category)
                else:
                    print(f"[DEBUG] Claude の回答からJSONを抽出できませんでした")
                    print(f"[DEBUG] Claude応答全体: {content}")
                    return self._mock_faq_generation(num_questions, category)
            else:
                print(f"[DEBUG] Claude API エラー - ステータス: {response.status_code}")
                return self._mock_faq_generation(num_questions, category)

        except Exception as e:
            print(f"[DEBUG] FAQ生成エラー: {e}")
            return self._mock_faq_generation(num_questions, category)

    def _mock_faq_generation(self, num_questions: int, category: str) -> list:
        """Claude API未設定時のモック FAQ 生成"""
        # 既存のFAQと承認待ちQ&Aを取得して重複を避ける
        existing_questions = [faq['question'] for faq in self.faq_data]
        self.load_pending_qa()
        pending_questions = [item['question'] for item in self.pending_qa if 'question' in item]
        all_existing_questions = existing_questions + pending_questions
        print(f"[DEBUG] モック生成 - 重複チェック対象: 既存FAQ {len(existing_questions)}件, 承認待ち {len(pending_questions)}件")

        base_mock_faqs = [
            {
                'question': 'H-1Bビザの申請に必要な最低学歴要件は何ですか？',
                'answer': 'H-1Bビザの申請には、通常4年制大学の学士号以上の学位が必要です。ただし、学位がない場合でも、3年間の実務経験が1年間の大学教育に相当するとみなされ、合計12年間の実務経験があれば申請可能な場合があります。',
                'keywords': 'H-1B;学歴要件;学士号;実務経験',
                'category': category
            },
            {
                'question': 'アメリカビザ面接で聞かれる一般的な質問は何ですか？',
                'answer': '面接では以下の質問がよく聞かれます：1)渡米目的、2)滞在期間、3)職歴や学歴、4)家族構成、5)帰国予定、6)経済状況など。回答は簡潔かつ正直に、必要な書類を準備して面接に臨むことが重要です。',
                'keywords': '面接;質問;準備;書類',
                'category': category
            },
            {
                'question': 'ESTA申請が拒否された場合はどうすればよいですか？',
                'answer': 'ESTA申請が拒否された場合、観光ビザ（B-2）または商用ビザ（B-1）を大使館で申請する必要があります。拒否理由を確認し、適切な書類を準備して面接予約を取ってください。ESTA拒否歴がある場合は面接で正直に説明することが重要です。',
                'keywords': 'ESTA;拒否;観光ビザ;B-1;B-2;面接',
                'category': category
            },
            {
                'question': 'アメリカでの滞在期間を延長することは可能ですか？',
                'answer': 'はい、可能です。滞在期限の45日前までにUSCIS（米国移民局）にForm I-539を提出して延長申請を行います。ただし、ESTA（ビザ免除プログラム）で入国した場合は延長できません。延長が承認されるには正当な理由と十分な資金証明が必要です。',
                'keywords': '滞在延長;I-539;USCIS;ESTA;資金証明',
                'category': category
            },
            {
                'question': '学生ビザ（F-1）から就労ビザ（H-1B）への変更手続きは？',
                'answer': 'F-1からH-1Bへの変更は「ステータス変更」申請で行います。雇用主がH-1B申請を行い、同時にUSCISにForm I-129とI-539を提出します。OPT期間中に申請することが多く、H-1Bの抽選に当選し承認されれば、アメリカを出国することなくステータス変更が可能です。',
                'keywords': 'F-1;H-1B;ステータス変更;I-129;I-539;OPT',
                'category': category
            },
            {
                'question': 'B-1/B-2ビザの有効期間と滞在期間の違いは何ですか？',
                'answer': 'ビザの有効期間は入国可能な期間、滞在期間は実際にアメリカに滞在できる期間です。B-1/B-2ビザは通常10年有効ですが、一回の滞在は最大6ヶ月までです。滞在期間はI-94で確認でき、この期間を超える場合は延長申請が必要です。',
                'keywords': 'B-1;B-2;有効期間;滞在期間;I-94',
                'category': category
            },
            {
                'question': 'グリーンカード申請中にアメリカを出国できますか？',
                'answer': 'グリーンカード申請中の出国は可能ですが、注意が必要です。調整申請（I-485）中の場合、事前許可（Advance Parole）の取得が必要です。許可なく出国すると申請が放棄されたとみなされる場合があります。',
                'keywords': 'グリーンカード;I-485;Advance Parole;出国',
                'category': category
            },
            {
                'question': 'L-1ビザの申請要件と取得までの期間は？',
                'answer': 'L-1ビザは企業内転勤者向けビザで、海外関連会社で1年以上勤務していることが要件です。L-1Aは管理職・役員向け、L-1Bは専門知識を持つ社員向けです。申請から取得まで通常3-6ヶ月かかります。',
                'keywords': 'L-1;企業内転勤;L-1A;L-1B;専門知識',
                'category': category
            },
            {
                'question': 'E-2投資家ビザの最低投資額はいくらですか？',
                'answer': 'E-2ビザに法定最低投資額はありませんが、実質的に事業を運営できる「相当額」の投資が必要です。一般的に15-20万ドル以上が目安とされます。投資額は事業の性質や規模により異なり、投資の実質性と継続性が重要です。',
                'keywords': 'E-2;投資家ビザ;投資額;事業運営',
                'category': category
            },
            {
                'question': 'O-1ビザ申請時の推薦状は何通必要ですか？',
                'answer': 'O-1ビザには最低8通の推薦状が推奨されています。業界の専門家、同僚、クライアントからの推薦状が効果的です。推薦者の資格と申請者との関係を明確に示し、具体的な功績や能力について詳述することが重要です。',
                'keywords': 'O-1;推薦状;専門家;功績;能力',
                'category': category
            }
        ]

        # 重複を避けながらFAQを生成
        def is_similar_question(question, existing_questions):
            """簡単な重複チェック（キーワードベース）"""
            question_lower = question.lower()
            for existing in existing_questions:
                existing_lower = existing.lower()
                # キーワードベースの簡易マッチング
                if (any(word in existing_lower for word in question_lower.split() if len(word) > 2) and
                    len(set(question_lower.split()) & set(existing_lower.split())) >= 2):
                    return True
            return False

        # 要求された数だけFAQを生成（重複を避けながら）
        mock_faqs = []
        print(f"[DEBUG] モック生成要求数: {num_questions}, 基本FAQ数: {len(base_mock_faqs)}")

        for i in range(num_questions):
            base_faq = base_mock_faqs[i % len(base_mock_faqs)].copy()

            # 重複チェック
            if not is_similar_question(base_faq['question'], all_existing_questions):
                if i >= len(base_mock_faqs):
                    # ベースを超える場合は質問を少し変更
                    base_faq['question'] = f"【追加生成】{base_faq['question']}"
                    base_faq['answer'] = f"【モック生成】{base_faq['answer']}"
                mock_faqs.append(base_faq)
                print(f"[DEBUG] モックFAQ{len(mock_faqs)}生成: {base_faq['question'][:30]}...")
            else:
                print(f"[DEBUG] 重複回避: {base_faq['question'][:30]}... をスキップ")

        # 足りない場合は追加のバリエーション生成
        while len(mock_faqs) < num_questions:
            additional_faq = {
                'question': f'【モック生成{len(mock_faqs)+1}】アメリカビザに関する質問です',
                'answer': f'【モック生成】これはテスト用の自動生成された回答です（{len(mock_faqs)+1}番目）。実際のビザ情報については専門家にご相談ください。',
                'keywords': f'モック;テスト;{category}',
                'category': category
            }
            mock_faqs.append(additional_faq)
            print(f"[DEBUG] 追加生成FAQ{len(mock_faqs)}: {additional_faq['question'][:30]}...")

        print(f"[DEBUG] 最終生成数: {len(mock_faqs)}")
        # 生成したFAQを履歴に保存
        if mock_faqs:
            self._save_to_generation_history(mock_faqs)
        return mock_faqs


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