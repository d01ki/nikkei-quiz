from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
import random
import os
from datetime import datetime

app = Flask(__name__)

# 設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nikkei_quiz_secret_key_2024')

# データベース設定
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # PostgreSQL URLの修正（RenderやHerokuの場合）
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # ローカル環境の場合はSQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# グローバル変数
db = None
User = None
QuizResult = None
UserStats = None
LoginForm = None
RegisterForm = None
login_manager = None
DB_INITIALIZED = False

# Flask-Loginの初期設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'

# ダミーのuser_loaderを設定
@login_manager.user_loader
def load_user_dummy(user_id):
    return None

def init_database():
    """データベース関連の初期化を遅延実行"""
    global db, User, QuizResult, UserStats, LoginForm, RegisterForm, DB_INITIALIZED
    
    if DB_INITIALIZED:
        return True
        
    try:
        # models.pyから既存のdbインスタンスをインポート
        from models import db as existing_db, User as _User, QuizResult as _QuizResult, UserStats as _UserStats
        from forms import LoginForm as _LoginForm, RegisterForm as _RegisterForm
        
        # 既存のdbインスタンスを使用（重複登録を回避）
        db = existing_db
        User = _User
        QuizResult = _QuizResult
        UserStats = _UserStats
        LoginForm = _LoginForm
        RegisterForm = _RegisterForm
        
        # アプリがまだ初期化されていない場合のみ初期化
        if not hasattr(db, 'app') or db.app is None:
            db.init_app(app)
        
        # 実際のuser_loaderで上書き
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
            
        # データベーステーブルを作成
        with app.app_context():
            db.create_all()
            print("✅ データベースを初期化しました")
            
        DB_INITIALIZED = True
        return True
    except Exception as e:
        print(f"⚠️ データベース初期化に失敗: {e}")
        print(f"   エラー詳細: {str(e)}")
        DB_INITIALIZED = False
        return False

# テンプレートで使用する変数を全体で利用可能にする
@app.context_processor
def inject_global_vars():
    """テンプレートで使用するグローバル変数を注入"""
    return {
        'db_available': DB_INITIALIZED,
        'current_user': current_user
    }

# サンプル問題データ
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

# ヘルスチェックエンドポイント
@app.route('/health')
def health_check():
    """ヘルスチェック用エンドポイント"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "database": DB_INITIALIZED,
        "python_version": os.sys.version
    })

# 起動時に1回だけデータベース初期化を実行
@app.before_request
def initialize_app():
    """アプリケーション初期化（最初のリクエスト時のみ）"""
    init_database()

# 認証ルート
@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン"""
    # 初期化されていない場合は今すぐ初期化を試行
    if not DB_INITIALIZED:
        init_database()
    
    if not DB_INITIALIZED:
        flash('システムメンテナンス中です。しばらくお待ちください。', 'warning')
        return redirect(url_for('index'))
        
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter(
                (User.username == form.username.data) | (User.email == form.username.data)
            ).first()
            
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                user.update_last_login()
                flash(f'ようこそ、{user.display_name or user.username}さん！', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('ユーザー名またはパスワードが間違っています。', 'error')
        except Exception as e:
            print(f"Login error: {e}")
            flash('ログイン処理中にエラーが発生しました。', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """ユーザー登録"""
    # 初期化されていない場合は今すぐ初期化を試行
    if not DB_INITIALIZED:
        init_database()
    
    if not DB_INITIALIZED:
        flash('システムメンテナンス中です。しばらくお待ちください。', 'warning')
        return redirect(url_for('index'))
        
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
def logout():
    """ログアウト"""
    if DB_INITIALIZED and current_user.is_authenticated:
        logout_user()
        flash('ログアウトしました。', 'info')
    return redirect(url_for('index'))

# メインルート
@app.route('/')
def index():
    """ホームページ"""
    try:
        if DB_INITIALIZED and current_user.is_authenticated:
            stats_obj = current_user.get_stats()
            stats = stats_obj.to_dict()
            # 最近の履歴を取得
            results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.timestamp.desc()).limit(5).all()
            stats['recent_history'] = [{
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
                'recent_history': []
            }
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        print(f"❌ ホームページエラー: {e}")
        return render_template('index.html', stats={'total_questions': 0, 'correct_answers': 0, 'categories': {}, 'recent_history': []})

@app.route('/quiz')
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
def dashboard():
    """ダッシュボードページ"""
    if not DB_INITIALIZED:
        flash('システムメンテナンス中です。', 'warning')
        return redirect(url_for('index'))
        
    if not current_user.is_authenticated:
        flash('ログインが必要です。', 'warning')
        return redirect(url_for('login'))
        
    try:
        stats_obj = current_user.get_stats()
        stats = stats_obj.to_dict()
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        print(f"❌ ダッシュボードエラー: {e}")
        return render_template('error.html', message='ダッシュボードの読み込みに失敗しました')

@app.route('/history')
def history():
    """履歴ページ"""
    if not DB_INITIALIZED:
        flash('システムメンテナンス中です。', 'warning')
        return redirect(url_for('index'))
        
    if not current_user.is_authenticated:
        flash('ログインが必要です。', 'warning')
        return redirect(url_for('login'))
        
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
def get_question():
    """ランダムな問題を取得"""
    try:
        questions = load_questions()
        
        if not questions:
            return jsonify({'error': '問題データがありません'}), 404
        
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
        
    except Exception as e:
        print(f"❌ get_question エラー: {e}")
        return jsonify({'error': f'サーバーエラー: {str(e)}'}), 500

@app.route('/api/submit_answer', methods=['POST'])
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
        
        # データベースに保存（データベースが利用可能な場合のみ）
        if DB_INITIALIZED and current_user.is_authenticated:
            try:
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
            except Exception as e:
                print(f"データベース保存エラー: {e}")
                if db:
                    db.session.rollback()
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': current_question.get('explanation', ''),
            'source': current_question.get('source', '')
        })
        
    except Exception as e:
        print(f"❌ submit_answer エラー: {e}")
        return jsonify({'error': f'サーバーエラー: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET', 'DELETE'])
def handle_stats():
    """統計データの取得・削除"""
    if not DB_INITIALIZED or not current_user.is_authenticated:
        return jsonify({'error': '認証が必要です'}), 401
        
    try:
        if request.method == 'GET':
            stats_obj = current_user.get_stats()
            return jsonify(stats_obj.to_dict())
        
        elif request.method == 'DELETE':
            QuizResult.query.filter_by(user_id=current_user.id).delete()
            stats = current_user.get_stats()
            stats.total_questions = 0
            stats.correct_answers = 0
            stats.set_categories({})
            db.session.commit()
            
            return jsonify({'message': '統計をリセットしました'})
    except Exception as e:
        if db:
            db.session.rollback()
        print(f"❌ handle_stats エラー: {e}")
        return jsonify({'error': f'サーバーエラー: {str(e)}'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', message='ページが見つかりません'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message='内部サーバーエラーが発生しました'), 500

if __name__ == '__main__':
    print("🚀 日経テスト練習アプリ（認証版）を起動中...")
    
    # 起動時にデータベース初期化を試行
    if init_database():
        print("📂 機能:")
        print("   - ✅ ユーザー登録・ログイン")
        print("   - ✅ PostgreSQL対応")
        print("   - ✅ セキュアなパスワードハッシュ化")
        print("   - ✅ 個人別統計管理")
    else:
        print("⚠️ データベース機能が無効です（基本機能のみ）")
        print("📂 利用可能機能:")
        print("   - ✅ 問題解答（統計なし）")
        print("   - ❌ ユーザー登録・ログイン")
    
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