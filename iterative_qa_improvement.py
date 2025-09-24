"""
対話的Q&A改善ツール
Claude Codeのような対話形式でQ&Aを改善する
"""
from faq_system import FAQSystem
import json
import os

class InteractiveQAImprovement:
    def __init__(self, csv_file: str):
        self.faq_system = FAQSystem(csv_file)
        self.improvement_history = []

    def start_improvement_session(self, user_question: str, current_answer: str):
        """改善セッションを開始"""
        print("=== Q&A改善セッション開始 ===")
        print(f"ユーザー質問: {user_question}")
        print(f"現在の回答: {current_answer}")
        print("-" * 50)

        session = {
            'user_question': user_question,
            'current_answer': current_answer,
            'iterations': []
        }

        # Step 1: 問題分析
        print("1. まず、現在の回答の問題点を分析します...")
        problem_analysis = self.analyze_problems(user_question, current_answer)
        print(f"問題分析結果: {problem_analysis}")

        # Step 2: 参考資料の提案
        print("\n2. 関連する参考資料を確認します...")
        relevant_docs = self.find_relevant_documents(user_question)
        print(f"関連文書: {len(relevant_docs)}件見つかりました")

        # Step 3: 初回改善案生成
        print("\n3. 初回改善案を生成します...")
        first_improvement = self.generate_improvement(
            user_question,
            current_answer,
            problem_analysis,
            relevant_docs
        )

        if first_improvement:
            session['iterations'].append(first_improvement)
            print(f"改善案: {first_improvement['question']}")
            print(f"回答: {first_improvement['answer'][:200]}...")

            # Step 4: 手動レビュー・追加改善
            if self.should_continue_improvement():
                print("\n4. さらなる改善を実行します...")
                self.refine_improvement(session)

        return session

    def analyze_problems(self, user_question: str, current_answer: str) -> str:
        """現在の回答の問題点を分析"""
        problems = []

        # 基本的な問題パターンをチェック
        if len(current_answer) < 50:
            problems.append("回答が短すぎて詳細が不足")

        if "詳細は" in current_answer and "確認" in current_answer:
            problems.append("具体的な情報が不足、他の情報源への誘導が多い")

        if not any(keyword in current_answer.lower() for keyword in ['申請', 'ビザ', '手続き']):
            problems.append("ビザ申請に関する具体的な情報が不足")

        if len(problems) == 0:
            problems.append("より具体的で実用的な情報を追加可能")

        return "；".join(problems)

    def find_relevant_documents(self, user_question: str) -> list:
        """関連する参考資料を検索"""
        relevant_docs = []

        try:
            reference_dir = os.path.join(os.path.dirname(__file__), 'reference_docs')
            if os.path.exists(reference_dir):
                for filename in os.listdir(reference_dir):
                    if filename.endswith('.txt'):
                        # 簡単なキーワードマッチング
                        if any(keyword in user_question.lower()
                               for keyword in ['h-1b', '専門職', 'h1b']) and 'h1b' in filename.lower():
                            relevant_docs.append(filename)
                        elif any(keyword in user_question.lower()
                                for keyword in ['学生', 'f-1', 'f1']) and 'student' in filename.lower():
                            relevant_docs.append(filename)
                        else:
                            relevant_docs.append(filename)  # 一般的な参考として
        except Exception as e:
            print(f"参考資料検索エラー: {e}")

        return relevant_docs

    def generate_improvement(self, user_question: str, current_answer: str,
                           problems: str, relevant_docs: list) -> dict:
        """改善案を生成（実際のプロジェクトではClaude APIを使用）"""
        # ここでは簡略化した例を返す
        return {
            'question': f"改善版：{user_question}",
            'answer': f"改善された回答：{current_answer} さらに詳細な情報として...",
            'keywords': "改善;詳細;実用的",
            'category': "改善版",
            'improvements_made': problems
        }

    def should_continue_improvement(self) -> bool:
        """改善を続けるかユーザーに確認"""
        while True:
            response = input("\nこの改善案で満足ですか？ (y)満足 / (n)さらに改善 / (q)終了: ").lower()
            if response in ['y', 'yes']:
                return False
            elif response in ['n', 'no']:
                return True
            elif response in ['q', 'quit']:
                return False
            else:
                print("y, n, q のいずれかを入力してください")

    def refine_improvement(self, session: dict):
        """改善案をさらに洗練"""
        print("\n追加の改善要求を入力してください:")
        additional_requirements = input("改善要求: ")

        if additional_requirements.strip():
            # 追加要求に基づいてさらに改善
            refined = self.generate_refinement(session, additional_requirements)
            if refined:
                session['iterations'].append(refined)
                print(f"洗練された回答: {refined['answer'][:200]}...")

    def generate_refinement(self, session: dict, additional_requirements: str) -> dict:
        """追加要求に基づく洗練"""
        last_iteration = session['iterations'][-1]
        return {
            'question': last_iteration['question'],
            'answer': f"{last_iteration['answer']} [追加要求「{additional_requirements}」を反映した内容]",
            'keywords': last_iteration['keywords'],
            'category': last_iteration['category'],
            'refinement': additional_requirements
        }

    def save_improved_qa(self, session: dict):
        """改善されたQ&AをFAQに追加"""
        if session['iterations']:
            best_iteration = session['iterations'][-1]
            self.faq_system.add_faq(
                question=best_iteration['question'],
                answer=best_iteration['answer'],
                keywords=best_iteration['keywords'],
                category=best_iteration['category']
            )
            self.faq_system.save_faq_data()
            print("✅ 改善されたQ&AをFAQに追加しました")

def main():
    """対話的改善のデモ"""
    improver = InteractiveQAImprovement('faq_data-1.csv')

    # 例：不満足だったQ&A
    user_q = "H-1Bビザの申請って難しいですか？"
    current_a = "専門職にはH-1Bビザが適しています。詳細は各ビザページをご確認いただくか担当者にお問い合わせください。"

    session = improver.start_improvement_session(user_q, current_a)

    # 改善結果をFAQに保存するか確認
    save = input("\n改善されたQ&AをFAQに保存しますか？ (y/n): ").lower()
    if save in ['y', 'yes']:
        improver.save_improved_qa(session)

if __name__ == "__main__":
    main()