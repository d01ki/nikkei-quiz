from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """ユーザーモデル"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # リレーション
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True, cascade='all, delete-orphan')
    user_stats = db.relationship('UserStats', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """パスワードをハッシュ化して保存"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """パスワードを検証"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """最終ログイン時刻を更新"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def get_stats(self):
        """ユーザー統計を取得"""
        if not self.user_stats:
            stats = UserStats(user_id=self.id)
            db.session.add(stats)
            db.session.commit()
        return self.user_stats
    
    def __repr__(self):
        return f'<User {self.username}>'

class QuizResult(db.Model):
    """クイズ結果モデル"""
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    user_answer = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    options = db.Column(db.Text)  # JSON string
    explanation = db.Column(db.Text)
    difficulty = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_options(self, options_list):
        """選択肢をJSON文字列で保存"""
        self.options = json.dumps(options_list, ensure_ascii=False)
    
    def get_options(self):
        """選択肢をリストとして取得"""
        if self.options:
            return json.loads(self.options)
        return []
    
    def __repr__(self):
        return f'<QuizResult {self.id}: {self.category}>'

class UserStats(db.Model):
    """ユーザー統計モデル"""
    __tablename__ = 'user_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    categories = db.Column(db.Text)  # JSON string for category stats
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_categories(self, categories_dict):
        """カテゴリ統計をJSON文字列で保存"""
        self.categories = json.dumps(categories_dict, ensure_ascii=False)
        self.last_updated = datetime.utcnow()
    
    def get_categories(self):
        """カテゴリ統計を辞書として取得"""
        if self.categories:
            return json.loads(self.categories)
        return {}
    
    def update_stats(self, category, is_correct):
        """統計を更新"""
        self.total_questions += 1
        if is_correct:
            self.correct_answers += 1
        
        # カテゴリ別統計更新
        categories = self.get_categories()
        if category not in categories:
            categories[category] = {'total': 0, 'correct': 0}
        
        categories[category]['total'] += 1
        if is_correct:
            categories[category]['correct'] += 1
        
        self.set_categories(categories)
        db.session.commit()
    
    def get_accuracy(self):
        """正答率を計算"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100
    
    def to_dict(self):
        """辞書形式で統計を返す（テンプレート用）"""
        return {
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'categories': self.get_categories(),
            'history': [],  # 履歴は別途取得
            'start_date': self.start_date.isoformat() if self.start_date else None
        }
    
    def __repr__(self):
        return f'<UserStats {self.user_id}: {self.total_questions} questions>'