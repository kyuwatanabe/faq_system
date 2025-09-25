from flask import Flask, render_template, request, jsonify, redirect, url_for
from faq_system import FAQSystem, find_similar_faqs
import json
import datetime

app = Flask(__name__)
faq_system = FAQSystem('faq_data-1.csv')

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """FAQ検索API"""
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': '質問を入力してください'}), 400

    # 最新データを再読み込み
    faq_system.load_faq_data('faq_data-1.csv')
    result, needs_confirmation = faq_system.get_best_answer(question)

    if needs_confirmation:
        return jsonify({
            'needs_confirmation': True,
            'suggested_question': result['question'],
            'answer': result['answer'],
            'matched_question': result['question']
        })
    else:
        return jsonify({
            'needs_confirmation': False,
            'answer': result,
            'matched_question': None
        })

@app.route('/admin')
def admin():
    """管理画面"""
    # 最新データを再読み込み
    faq_system.load_faq_data('faq_data-1.csv')
    faqs = faq_system.faq_data
    print(f"[DEBUG] 管理画面: FAQデータ件数 = {len(faqs)}")
    print(f"[DEBUG] 最初の3件: {[faq.get('question', '')[:30] for faq in faqs[:3]]}")
    return render_template('admin.html', faqs=faqs)

@app.route('/admin/add', methods=['POST'])
def add_faq():
    """FAQ追加"""
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()

    if question and answer:
        faq_system.add_faq(question, answer)
        faq_system.save_faq_data()

    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:index>', methods=['POST'])
def edit_faq(index):
    """FAQ編集"""
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()

    if faq_system.edit_faq(index, question if question else None, answer if answer else None):
        faq_system.save_faq_data()

    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:index>', methods=['POST'])
def delete_faq(index):
    """FAQ削除"""
    faq_system.delete_faq(index)
    faq_system.save_faq_data()
    return redirect(url_for('admin'))

@app.route('/interactive_improvement')
def interactive_improvement():
    """対話的改善画面"""
    return render_template('interactive_improvement.html')

@app.route('/admin/review')
def review_pending():
    """承認待ちQ&A一覧"""
    # 最新データを再読み込み
    faq_system.load_pending_qa()
    pending_items = faq_system.pending_qa
    print(f"[DEBUG] 承認待ち画面: 承認待ちアイテム数 = {len(pending_items)}")
    return render_template('review_pending.html', pending_items=pending_items)

@app.route('/admin/approve/<qa_id>', methods=['POST'])
def approve_qa(qa_id):
    """Q&Aを承認してFAQに追加"""
    if faq_system.approve_pending_qa(qa_id):
        faq_system.save_faq_data()
        print(f"[DEBUG] Q&A承認成功: {qa_id}")
    else:
        print(f"[DEBUG] Q&A承認失敗: {qa_id}")
    return redirect(url_for('review_pending'))

@app.route('/admin/reject/<qa_id>', methods=['POST'])
def reject_qa(qa_id):
    """Q&Aを却下"""
    if faq_system.reject_pending_qa(qa_id):
        print(f"[DEBUG] Q&A却下成功: {qa_id}")
    else:
        print(f"[DEBUG] Q&A却下失敗: {qa_id}")
    return redirect(url_for('review_pending'))

@app.route('/admin/edit_pending/<qa_id>', methods=['POST'])
def edit_pending_qa(qa_id):
    """承認待ちQ&Aを編集"""
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    keywords = request.form.get('keywords', '').strip()
    category = request.form.get('category', '').strip()

    if faq_system.edit_pending_qa(qa_id, question, answer, keywords, category):
        print(f"[DEBUG] 承認待ちQ&A編集成功: {qa_id}")
    else:
        print(f"[DEBUG] 承認待ちQ&A編集失敗: {qa_id}")

    return redirect(url_for('check_duplicates', qa_id=qa_id))

@app.route('/admin/check_duplicates/<qa_id>')
def check_duplicates(qa_id):
    """承認待ちQ&Aの重複チェック"""
    try:
        # 承認待ちQ&Aを取得
        faq_system.load_pending_qa()
        pending_item = None
        for item in faq_system.pending_qa:
            if item['id'] == qa_id:
                pending_item = item
                break

        if not pending_item:
            print(f"[DEBUG] 承認待ちアイテムが見つかりません: {qa_id}")
            return redirect(url_for('review_pending'))

        # 類似FAQ検索
        faq_system.load_faq_data('faq_data-1.csv')
        similar_faqs = find_similar_faqs(faq_system, pending_item['question'])

        print(f"[DEBUG] 重複チェック - 質問: {pending_item['question']}")
        print(f"[DEBUG] 類似FAQ数: {len(similar_faqs)}")

        return render_template('check_duplicates.html',
                             pending_item=pending_item,
                             similar_faqs=similar_faqs)
    except Exception as e:
        print(f"[ERROR] 重複チェックでエラー: {e}")
        import traceback
        traceback.print_exc()
        return f"エラーが発生しました: {e}", 500

@app.route('/admin/auto_generate', methods=['POST'])
def auto_generate_faqs():
    """FAQ自動生成API"""
    try:
        source_file = request.form.get('source_file', '').strip()
        num_questions = int(request.form.get('num_questions', 3))
        category = request.form.get('category', 'AI生成').strip()

        if not source_file:
            return jsonify({'success': False, 'message': 'ソースファイルを選択してください'})

        if num_questions < 1 or num_questions > 10:
            return jsonify({'success': False, 'message': '生成数は1-10の範囲で指定してください'})

        # PDFファイルのパスを構築
        import os
        reference_dir = r'C:\Users\GF001\Desktop\システム開発\faq_system250924\reference_docs'
        pdf_path = os.path.join(reference_dir, source_file)

        if not os.path.exists(pdf_path):
            return jsonify({'success': False, 'message': f'ファイルが見つかりません: {source_file}'})

        print(f"[DEBUG] FAQ自動生成開始 - ファイル: {source_file}, 数: {num_questions}")

        # FAQ生成
        generated_faqs = faq_system.generate_faqs_from_document(pdf_path, num_questions, category)

        if not generated_faqs:
            return jsonify({'success': False, 'message': 'FAQの生成に失敗しました'})

        # 承認待ちキューに追加
        added_count = 0
        for faq in generated_faqs:
            try:
                qa_id = faq_system.add_pending_qa(
                    question=faq.get('question', ''),
                    answer=faq.get('answer', ''),
                    keywords=faq.get('keywords', ''),
                    category=faq.get('category', category),
                    user_question=f"[自動生成] {source_file}から生成"
                )
                added_count += 1
                print(f"[DEBUG] 承認待ちQ&Aに追加: {qa_id}")
            except Exception as e:
                print(f"[DEBUG] 承認待ちQ&A追加エラー: {e}")

        if added_count > 0:
            return jsonify({
                'success': True,
                'generated_count': added_count,
                'message': f'{added_count}件のQ&Aを承認待ちキューに追加しました'
            })
        else:
            return jsonify({'success': False, 'message': '承認待ちキューへの追加に失敗しました'})

    except Exception as e:
        print(f"[DEBUG] FAQ自動生成エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'エラーが発生しました: {str(e)}'})

@app.route('/feedback', methods=['POST'])
def feedback():
    """ユーザーフィードバックを処理"""
    data = request.get_json()
    satisfied = data.get('satisfied')
    user_question = data.get('user_question')
    matched_question = data.get('matched_question')
    matched_answer = data.get('matched_answer')

    if not satisfied and user_question:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 不満足なQ&Aを記録
        faq_system.save_unsatisfied_qa(user_question, matched_question, matched_answer, timestamp)

        # Claude API が設定されているかチェック
        import os
        api_key = os.getenv('CLAUDE_API_KEY')
        print(f"[DEBUG] CLAUDE_API_KEY exists: {bool(api_key)}")
        if api_key:
            print(f"[DEBUG] API key starts with: {api_key[:10] if len(api_key) > 10 else 'too short'}")

        if api_key:
            # Claude で自動改善を試行
            try:
                print(f"[DEBUG] Claude API で自動改善開始: {user_question}")
                improvement_success = faq_system.auto_improve_qa(user_question, matched_question, matched_answer)
                if improvement_success:
                    print(f"[DEBUG] 自動改善成功")
                    return jsonify({
                        'status': 'success',
                        'message': 'フィードバックありがとうございます。【Claude API】が改善されたQ&Aを自動生成しました。管理者による承認後にFAQに追加されます。'
                    })
                else:
                    print(f"[DEBUG] 自動改善失敗")
                    return jsonify({
                        'status': 'success',
                        'message': 'フィードバックありがとうございます。改善案の生成に失敗しましたが、記録いたしました。'
                    })
            except Exception as e:
                print(f"自動改善エラー: {e}")
                return jsonify({
                    'status': 'success',
                    'message': 'フィードバックありがとうございます。記録いたしました。（Claude API エラー）'
                })
        else:
            # Claude API キー未設定の場合、モック機能を使用
            print(f"[DEBUG] Claude API キー未設定。モック改善機能を使用します")
            try:
                improvement_success = faq_system.auto_improve_qa(user_question, matched_question, matched_answer)
                if improvement_success:
                    print(f"[DEBUG] モック改善成功")
                    return jsonify({
                        'status': 'success',
                        'message': 'フィードバックありがとうございます。【モック機能】が改善されたQ&Aを自動生成しました。管理者による承認後にFAQに追加されます。'
                    })
                else:
                    print(f"[DEBUG] モック改善失敗")
                    return jsonify({
                        'status': 'success',
                        'message': 'フィードバックありがとうございます。改善案の生成に失敗しましたが、記録いたしました。'
                    })
            except Exception as e:
                print(f"モック改善エラー: {e}")
                return jsonify({
                    'status': 'success',
                    'message': 'フィードバックありがとうございます。記録いたしました。（モック機能エラー）'
                })

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    import os
    # 起動時に環境変数をチェック
    api_key = os.getenv('CLAUDE_API_KEY')
    print(f"[STARTUP] CLAUDE_API_KEY is {'set' if api_key else 'NOT set'}")
    if api_key:
        print(f"[STARTUP] API key starts with: {api_key[:10]}...")

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)