from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
import random
import os
from datetime import datetime
from models import db, User, QuizResult, UserStats
from forms import LoginForm, RegisterForm

app = Flask(__name__)

# 設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nikkei_quiz_secret_key_2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quiz.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# PostgreSQL URLの修正（RenderやHerokuの場合）
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

# 初期化
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# サンプル問題データ（既存のものを保持）
SAMPLE_QUESTIONS = [
    {
        "id": "sample_001",
        "category": "基礎知識",
        "question": "日経平均株価について、正しい説明はどれか。",
        "options": [
            "東証3市場の代表的な500社を選んで算出している",
            "東証株価指数に比べ市場全体の時価総額の動きを反映しやすい",
            "バブル崩壊後の最安値で1万円を割ったことがある",
            "算出方式は米国のS&Pやナスダック総合指数と同じである"
        ],
        "correct_answer": 2,
        "explanation": "日経平均株価の最安値は終値では2009年の7054円98銭でした。東証プライム上場企業から選んだ225社の株価で算出する指数です。",
        "difficulty": "中級",
        "source": "日経TEST公式テキスト&問題集 2024-25年版"
    },
    {
        "id": "sample_002",
        "category": "実践知識",
        "question": "最近のドラッグストア業界について、正しい記述はどれか。",
        "options": [
            "食品スーパーやコンビニから顧客を取り込み業績を伸ばした",
            "全国の店舗数は2万店を目前に頭打ちになった",
            "イオン系を除きプライベートブランド商品を発売していない",
            "総合商社も加わった業界再編で大きく3陣営に分かれている"
        ],
        "correct_answer": 0,
        "explanation": "ドラッグストアは粗利の高い医薬品で収益を確保し、食品や日用品を安く売るビジネスモデルで成長しました。競合してスーパーが閉店するケースも目立っています。",
        "difficulty": "中級",
        "source": "日経TEST公式テキスト&問題集 2024-25年版"
    },
    {
        "id": "sample_003",
        "category": "視野の広さ",
        "question": "金の国際相場の取引単位となる1トロイオンスは約何グラムか。",
        "options": [
            "10グラム",
            "30グラム",
            "100グラム",
            "150グラム"
        ],
        "correct_answer": 1,
        "explanation": "正確には1トロイオンス＝31.1035グラムです。金は有史以来採掘された総量が約20万トン、五輪の水泳競技で使う国際基準プール約4杯分とよくいわれます。",
        "difficulty": "初級",
        "source": "日経TEST公式テキスト&問題集 2024-25年版"
    },
    {
        "id": "sample_004",
        "category": "知識を知恵にする力",
        "question": "生成AI（人工知能）が強みを発揮する分野として、ふさわしくないと考えられるのはどれか。",
        "options": [
            "カスタマーサポートの負荷軽減",
            "膨大なデータに基づく事実確認",
            "文章の要約や正確な多言語翻訳",
            "新製品やサービスの紹介文作成"
        ],
        "correct_answer": 1,
        "explanation": "生成AIはハルシネーション（幻覚）と呼ばれる『もっともらしいが事実と異なる内容』を答えることが多くなります。日進月歩の技術ですが、『事実確認』はまだふさわしくないと考えられます。",
        "difficulty": "中級",
        "source": "日経TEST公式テキスト&問題集 2024-25年版"
    },
    {
        "id": "sample_005",
        "category": "知恵を活用する力",
        "question": "株式を上場する企業が非上場化する、経営陣が参加する買収（MBO）について、間違っている記述はどれか。",
        "options": [
            "他社からの企業買収の防衛策としても活用される",
            "非上場化した後に再上場することはできない",
            "中長期の視点で改革に取り組むことができる",
            "投資ファンドや銀行が関与する事例が多い"
        ],
        "correct_answer": 1,
        "explanation": "上場廃止後に再上場する道もあり、外食のすかいらーくホールディングスや、米国ではパソコンのデル・テクノロジーズなどの事例があります。",
        "difficulty": "上級",
        "source": "日経TEST公式テキスト&問題集 2024-25年版"
    }
]

def load_questions():
    """問題データを読み込む関数"""
    try:
        if os.path.exists('data/questions.json'):
            with open('data/questions.json', 'r', encoding='utf-8') as f:
                questions = json.load(f)
                if questions and len(questions) > 0:
                    print(f"✅ 問題データを読み込みました: {len(questions)}問")
                    return questions
                else:
                    print("⚠️ 問題データが空です。サンプルデータを使用します")
        else:
            print("⚠️ data/questions.jsonが見つかりません。サンプルデータを使用します")
    except Exception as e:
        print(f"❌ 問題データ読み込みエラー: {e}")
    
    print(f"📚 サンプル問題データを使用します: {len(SAMPLE_QUESTIONS)}問")
    return SAMPLE_QUESTIONS

# 認証ルート
@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # ユーザー名またはメールアドレスでユーザーを検索
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            flash(f'ようこそ、{user.display_name or user.username}さん！', 'success')
            
            # リダイレクト先の処理
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """ユーザー登録"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                display_name=form.display_name.data or form.username.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            # 統計データを初期化
            stats = UserStats(user_id=user.id)
            db.session.add(stats)
            db.session.commit()
            
            flash('登録が完了しました！ログインしてください。', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('登録中にエラーが発生しました。再度お試しください。', 'error')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """ログアウト"""
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('index'))

# メインルート
@app.route('/')
def index():
    """ホームページ"""
    try:
        if current_user.is_authenticated:
            stats_obj = current_user.get_stats()
            stats = stats_obj.to_dict()
            # 履歴を追加
            results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.timestamp.desc()).limit(10).all()
            stats['history'] = [{
                'question': result.question_text,
                'category': result.category,
                'is_correct': result.is_correct,
                'timestamp': result.timestamp.isoformat()
            } for result in results]
        else:
            stats = {
                'total_questions': 0,
                'correct_answers': 0,
                'categories': {},
                'history': []
            }
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        print(f"❌ ホームページエラー: {e}")
        return render_template('error.html', message='ホームページの読み込みに失敗しました')

@app.route('/quiz')
@login_required
def quiz():
    """クイズページ"""
    try:
        questions = load_questions()
        if not questions:
            return render_template('error.html', message='問題データが見つかりません')
        
        # セッションをクリア
        session.clear()
        return render_template('quiz.html')
    except Exception as e:
        print(f"❌ クイズページエラー: {e}")
        return render_template('error.html', message='クイズページの読み込みに失敗しました')

@app.route('/dashboard')
@login_required
def dashboard():
    """ダッシュボードページ"""
    try:
        stats_obj = current_user.get_stats()
        stats = stats_obj.to_dict()
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        print(f"❌ ダッシュボードエラー: {e}")
        return render_template('error.html', message='ダッシュボードの読み込みに失敗しました')

@app.route('/history')
@login_required
def history():
    """履歴ページ"""
    try:
        stats_obj = current_user.get_stats()
        stats = stats_obj.to_dict()
        
        # 履歴を取得
        results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.timestamp.desc()).all()
        stats['history'] = [{
            'question_id': result.question_id,
            'question': result.question_text,
            'category': result.category,
            'user_answer': result.user_answer,
            'correct_answer': result.correct_answer,
            'options': result.get_options(),
            'explanation': result.explanation,
            'is_correct': result.is_correct,
            'timestamp': result.timestamp.isoformat()
        } for result in results]
        
        return render_template('history.html', stats=stats)
    except Exception as e:
        print(f"❌ 履歴ページエラー: {e}")
        return render_template('error.html', message='履歴ページの読み込みに失敗しました')

# API エンドポイント
@app.route('/api/get_question')
@login_required
def get_question():
    """ランダムな問題を取得"""
    try:
        questions = load_questions()
        print(f"📝 利用可能な問題数: {len(questions)}")
        
        if not questions:
            return jsonify({'error': '問題データがありません'}), 404
        
        question = random.choice(questions)
        print(f"🎯 選択された問題: {question['id']} - {question['category']}")
        
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
        
    except Exception as e:
        print(f"❌ get_question エラー: {e}")
        return jsonify({'error': f'サーバーエラー: {str(e)}'}), 500

@app.route('/api/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """回答を送信"""
    try:
        data = request.json
        if not data or 'answer' not in data:
            return jsonify({'error': '回答データが不正です'}), 400
            
        user_answer = data.get('answer')
        
        current_question = session.get('current_question')
        if not current_question:
            return jsonify({'error': '問題が見つかりません'}), 400
        
        correct_answer = current_question['correct_answer']
        is_correct = user_answer == correct_answer
        
        print(f"📊 回答結果 - ユーザー: {user_answer}, 正解: {correct_answer}, 結果: {'✅' if is_correct else '❌'}")
        
        # データベースに結果を保存
        result = QuizResult(
            user_id=current_user.id,
            question_id=current_question['id'],
            question_text=current_question['question'],
            category=current_question['category'],
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            explanation=current_question.get('explanation', ''),
            difficulty=current_question.get('difficulty', '中級')
        )
        result.set_options(current_question['options'])
        
        db.session.add(result)
        
        # 統計を更新
        stats = current_user.get_stats()
        stats.update_stats(current_question['category'], is_correct)
        
        db.session.commit()
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': current_question.get('explanation', ''),
            'source': current_question.get('source', '')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ submit_answer エラー: {e}")
        return jsonify({'error': f'サーバーエラー: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET', 'DELETE'])
@login_required
def handle_stats():
    """統計データの取得・削除"""
    try:
        if request.method == 'GET':
            stats_obj = current_user.get_stats()
            return jsonify(stats_obj.to_dict())
        
        elif request.method == 'DELETE':
            # ユーザーの全データを削除
            QuizResult.query.filter_by(user_id=current_user.id).delete()
            stats = current_user.get_stats()
            stats.total_questions = 0
            stats.correct_answers = 0
            stats.set_categories({})
            db.session.commit()
            
            return jsonify({'message': '統計をリセットしました'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ handle_stats エラー: {e}")
        return jsonify({'error': f'サーバーエラー: {str(e)}'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', message='ページが見つかりません'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message='内部サーバーエラーが発生しました'), 500

# データベース初期化
def init_db():
    """データベースを初期化"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ データベースを初期化しました")
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")

if __name__ == '__main__':
    print("🚀 日経テスト練習アプリ（認証版）を起動中...")
    
    # データベース初期化
    init_db()
    
    print("📂 機能:")
    print("   - ✅ ユーザー登録・ログイン")
    print("   - ✅ PostgreSQL対応")
    print("   - ✅ セキュアなパスワードハッシュ化")
    print("   - ✅ 個人別統計管理")
    print("")
    print("🌐 アクセス方法:")
    print("   - ローカル: http://localhost:5000")
    print("   - ネットワーク: http://0.0.0.0:5000")
    print("")
    print("⏹️ 停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    # 本番環境での設定
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)