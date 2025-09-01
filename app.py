from flask import Flask, render_template, request, jsonify, session
import json
import random
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'nikkei_quiz_secret_key_2024'

# 問題データを読み込む関数
def load_questions():
    with open('data/questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# ユーザー統計を保存する関数
def save_user_stats(user_stats):
    if not os.path.exists('data'):
        os.makedirs('data')
    with open('data/user_stats.json', 'w', encoding='utf-8') as f:
        json.dump(user_stats, f, ensure_ascii=False, indent=2)

# ユーザー統計を読み込む関数
def load_user_stats():
    try:
        with open('data/user_stats.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'total_questions': 0,
            'correct_answers': 0,
            'categories': {},
            'history': [],
            'start_date': datetime.now().isoformat()
        }

@app.route('/')
def index():
    """ホームページ"""
    stats = load_user_stats()
    return render_template('index.html', stats=stats)

@app.route('/quiz')
def quiz():
    """クイズページ"""
    questions = load_questions()
    # セッションをクリア
    session.clear()
    return render_template('quiz.html')

@app.route('/dashboard')
def dashboard():
    """ダッシュボードページ"""
    stats = load_user_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/api/get_question')
def get_question():
    """ランダムな問題を取得"""
    questions = load_questions()
    if not questions:
        return jsonify({'error': '問題が見つかりません'})
    
    question = random.choice(questions)
    
    # セッションに現在の問題を保存
    session['current_question'] = question
    
    # 正解を除いて返す
    return jsonify({
        'id': question['id'],
        'category': question['category'],
        'question': question['question'],
        'options': question['options'],
        'difficulty': question.get('difficulty', '中級')
    })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    """回答を送信"""
    data = request.json
    user_answer = data.get('answer')
    
    current_question = session.get('current_question')
    if not current_question:
        return jsonify({'error': '問題が見つかりません'})
    
    correct_answer = current_question['correct_answer']
    is_correct = user_answer == correct_answer
    
    # 統計を更新
    stats = load_user_stats()
    stats['total_questions'] += 1
    if is_correct:
        stats['correct_answers'] += 1
    
    # カテゴリ別統計
    category = current_question['category']
    if category not in stats['categories']:
        stats['categories'][category] = {'total': 0, 'correct': 0}
    stats['categories'][category]['total'] += 1
    if is_correct:
        stats['categories'][category]['correct'] += 1
    
    # 履歴に追加
    stats['history'].append({
        'question_id': current_question['id'],
        'question': current_question['question'],
        'category': category,
        'user_answer': user_answer,
        'correct_answer': correct_answer,
        'is_correct': is_correct,
        'timestamp': datetime.now().isoformat()
    })
    
    # 最新20件のみ保持
    stats['history'] = stats['history'][-20:]
    
    save_user_stats(stats)
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': correct_answer,
        'explanation': current_question.get('explanation', ''),
        'source': current_question.get('source', '')
    })

@app.route('/api/stats')
def get_stats():
    """統計データを取得"""
    return jsonify(load_user_stats())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)