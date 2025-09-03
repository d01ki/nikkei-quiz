from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
import random
import os
from datetime import datetime
import sys

app = Flask(__name__)

# 設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nikkei_quiz_secret_key_2024')

# データベース設定
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✅ データベースURL設定完了")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    print("⚠️ SQLiteデータベースを使用します")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# グローバル変数の初期化
db = None
User = None
QuizResult = None
UserStats = None
LoginForm = None
RegisterForm = None

# Flask-Loginの初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'

DB_INITIALIZED = False

# user_loader
@login_manager.user_loader
def load_user(user_id):
    if User and DB_INITIALIZED:
        try:
            return User.query.get(int(user_id))
        except:
            return None
    return None

# ダミーフィールドクラス
class DummyField:
    def __init__(self, label_text=""):
        self.data = ""
        self.label_text = label_text
    
    def label(self, **kwargs):
        return f'<label {" ".join(f"{k}=\"{v}\"" for k, v in kwargs.items())}>{self.label_text}</label>'
    
    def __call__(self, **kwargs):
        return f'<input type="text" disabled placeholder="データベース接続中..." {" ".join(f"{k}=\"{v}\"" for k, v in kwargs.items())} />'

# ダミーフォームクラス（DB接続失敗時用）
class DummyForm:
    def __init__(self):
        self.username = DummyField("ユーザー名")
        self.email = DummyField("メールアドレス")
        self.display_name = DummyField("表示名（任意）")
        self.password = DummyField("パスワード")
        self.password2 = DummyField("パスワード確認")
        self.remember_me = DummyField("ログイン状態を保持")
        self.submit = DummyField()
    
    def hidden_tag(self):
        return ""
    
    def validate_on_submit(self):
        return False

def init_database():
    """データベース関連の初期化"""
    global db, User, QuizResult, UserStats, LoginForm, RegisterForm, DB_INITIALIZED
    
    if DB_INITIALIZED:
        return True
        
    try:
        print("🔍 データベース初期化を開始...")
        
        # モジュールのインポート
        try:
            import models
            import forms
            print("✅ モジュールのインポートに成功")
        except ImportError as e:
            print(f"❌ モジュールインポートエラー: {e}")
            return False
        
        # グローバル変数に代入
        db = models.db
        User = models.User
        QuizResult = models.QuizResult
        UserStats = models.UserStats
        LoginForm = forms.LoginForm
        RegisterForm = forms.RegisterForm
        
        # SQLAlchemyの初期化（重複チェック）
        try:
            # 既にアプリに登録されているかチェック
            if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
                db.init_app(app)
                print("✅ SQLAlchemyの初期化に成功")
            else:
                print("⚠️ SQLAlchemy は既に初期化されています")
        except Exception as e:
            if "already been registered" in str(e):
                print("⚠️ SQLAlchemy already registered, using existing instance")
            else:
                print(f"❌ SQLAlchemy初期化エラー: {e}")
                return False
        
        # アプリケーションコンテキスト内でテーブル作成
        try:
            with app.app_context():
                # データベース接続テスト
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                print("✅ データベース接続テストに成功")
                
                # テーブル作成
                db.create_all()
                print("✅ データベーステーブルを作成しました")
                
        except Exception as e:
            print(f"❌ データベーステーブル作成エラー: {e}")
            return False
            
        DB_INITIALIZED = True
        print("✅ データベース初期化完了")
        return True
        
    except Exception as e:
        print(f"❌ データベース初期化に失敗: {e}")
        import traceback
        traceback.print_exc()
        DB_INITIALIZED = False
        return False

# テンプレート用のコンテキストプロセッサ
@app.context_processor
def inject_global_vars():
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
    }
]

def load_questions():
    try:
        if os.path.exists('data/questions.json'):
            with open('data/questions.json', 'r', encoding='utf-8') as f:
                questions = json.load(f)
                if questions and len(questions) > 0:
                    print(f"✅ 問題データを読み込みました: {len(questions)}問")
                    return questions
        else:
            print("⚠️ data/questions.jsonが見つかりません。サンプルデータを使用します")
    except Exception as e:
        print(f"❌ 問題データ読み込みエラー: {e}")
    
    print(f"📚 サンプル問題データを使用します: {len(SAMPLE_QUESTIONS)}問")
    return SAMPLE_QUESTIONS

@app.route('/health')
def health_check():
    try:
        db_status = "disconnected"
        if DB_INITIALIZED and db:
            try:
                from sqlalchemy import text
                with app.app_context():
                    db.session.execute(text('SELECT 1'))
                    db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"
        
        return jsonify({
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "environment": os.environ.get('FLASK_ENV', 'development')
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "database": "error"
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    # データベースが初期化されていない場合は再試行
    if not DB_INITIALIZED:
        init_success = init_database()
        if not init_success:
            flash('データベース接続中です。しばらくお待ちください。', 'warning')
            return render_template('auth/login.html', form=DummyForm(), db_error=True)
        
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
    # データベースが初期化されていない場合は再試行
    if not DB_INITIALIZED:
        init_success = init_database()
        if not init_success:
            flash('データベース接続中です。しばらくお待ちください。', 'warning')
            return render_template('auth/register.html', form=DummyForm(), db_error=True)
        
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
    if DB_INITIALIZED and current_user.is_authenticated:
        logout_user()
        flash('ログアウトしました。', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    try:
        if DB_INITIALIZED and current_user.is_authenticated:
            stats_obj = current_user.get_stats()
            stats = stats_obj.to_dict()
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
    try:
        questions = load_questions()
        if not questions:
            return render_template('error.html', message='問題データが見つかりません')
        
        session.clear()
        return render_template('quiz.html')
    except Exception as e:
        print(f"❌ クイズページエラー: {e}")
        return render_template('error.html', message='クイズページの読み込みに失敗しました')

@app.route('/dashboard')
def dashboard():
    if not DB_INITIALIZED:
        flash('データベース接続中です。', 'warning')
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
    if not DB_INITIALIZED:
        flash('データベース接続中です。', 'warning')
        return redirect(url_for('index'))
        
    if not current_user.is_authenticated:
        flash('ログインが必要です。', 'warning')
        return redirect(url_for('login'))
        
    try:
        stats_obj = current_user.get_stats()
        stats = stats_obj.to_dict()
        
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

@app.route('/api/get_question')
def get_question():
    try:
        questions = load_questions()
        
        if not questions:
            return jsonify({'error': '問題データがありません'}), 404
        
        question = random.choice(questions)
        session['current_question'] = question
        
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

# アプリケーション起動時に初期化を実行
init_database()

if __name__ == '__main__':
    print("🚀 日経テスト練習アプリ（認証版）を起動中...")
    
    if DB_INITIALIZED:
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
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
