# 🔒 認証機能付き日経クイズアプリ - 開発ブランチ

このブランチ（`feature/user-authentication`）では、ユーザー認証機能とPostgreSQL対応を追加しました。

## ✨ 新機能

### 🔐 認証システム
- **ユーザー登録**: メール、ユーザー名、パスワード
- **ログイン/ログアウト**: セッション管理
- **パスワードハッシュ化**: bcrypt使用
- **フォームバリデーション**: Flask-WTF使用

### 🗄️ データベース対応
- **PostgreSQL**: 本番環境対応
- **SQLAlchemy**: ORM使用
- **個人データ分離**: ユーザー別統計管理
- **データ永続化**: 安全なデータ保存

### 🎯 機能強化
- **個人別統計**: ユーザー毎の学習記録
- **セキュアAPI**: ログイン必須のエンドポイント
- **レスポンシブ認証UI**: モダンなフォームデザイン

## 🚀 テスト方法

### ローカル開発
```bash
# 新しい依存関係をインストール
pip install -r requirements.txt

# データベースを初期化（初回のみ）
python app.py  # 自動でテーブル作成

# アプリ起動
python app.py
```

### 本番環境（Render）
1. **PostgreSQL設定**: Render ダッシュボードでPostgreSQLを作成
2. **環境変数設定**:
   - `DATABASE_URL`: PostgreSQLの接続URL
   - `SECRET_KEY`: セキュアな秘密鍵
   - `FLASK_ENV`: `production`

## 📊 データベーススキーマ

### Users テーブル
- id (主キー)
- username (一意)
- email (一意)
- password_hash
- display_name
- created_at
- last_login

### QuizResult テーブル
- id (主キー)
- user_id (外部キー)
- question_id
- question_text
- category
- user_answer
- correct_answer
- is_correct
- options (JSON)
- explanation
- timestamp

### UserStats テーブル
- id (主キー)
- user_id (外部キー)
- total_questions
- correct_answers
- categories (JSON)
- start_date
- last_updated

## 🔒 セキュリティ機能

- **パスワードハッシュ化**: Werkzeug使用
- **CSRF保護**: Flask-WTF使用
- **セッション管理**: Flask-Login使用
- **SQLインジェクション対策**: SQLAlchemy ORM使用
- **入力検証**: WTForms バリデータ

## 🎨 UI/UX改善

- **認証フォーム**: モダンなデザイン
- **フラッシュメッセージ**: 自動非表示
- **ユーザー表示**: ナビゲーションバーにユーザー名
- **認証状態対応**: ログイン/ログアウト状態でUI変更

## ⚡ パフォーマンス

- **データベースインデックス**: username, emailにインデックス
- **効率的クエリ**: SQLAlchemy最適化
- **セッション管理**: 適切な有効期限

## 🧪 テスト項目

### 基本機能
- [ ] ユーザー登録（正常系）
- [ ] ユーザー登録（異常系：重複など）
- [ ] ログイン（正常系）
- [ ] ログイン（異常系：間違いなど）
- [ ] ログアウト
- [ ] ページアクセス権限

### データ機能
- [ ] 問題解答（ログイン後）
- [ ] 統計更新
- [ ] 履歴保存
- [ ] データベース永続化

### セキュリティ
- [ ] 未ログイン時のリダイレクト
- [ ] パスワードハッシュ化確認
- [ ] CSRF対策
- [ ] セッション管理

## 💾 データ移行

既存のJSONデータから新しいPostgreSQLへの移行方法：

```python
# migration_script.py (参考)
import json
from app import app, db, User, QuizResult, UserStats

def migrate_json_to_db():
    with app.app_context():
        # 既存JSONデータを読み込み
        # PostgreSQLに移行
        pass
```

## 📝 変更履歴

### 追加ファイル
- `models.py`: データベースモデル
- `forms.py`: 認証フォーム
- `templates/auth/login.html`: ログインページ
- `templates/auth/register.html`: 登録ページ

### 更新ファイル
- `app.py`: 認証機能追加
- `requirements.txt`: 新しい依存関係
- `templates/base.html`: 認証UI追加
- `templates/index.html`: 認証対応

## 🐛 既知の問題

- [ ] 初回デプロイ時のデータベース初期化
- [ ] パスワードリセット機能未実装
- [ ] メール認証機能未実装

## 🚀 次のステップ

1. **テスト完了後**に`main`ブランチにマージ
2. **パスワードリセット機能**追加
3. **メール認証機能**追加
4. **管理者機能**追加

---

**⚠️ 注意**: このブランチは開発用です。テスト完了後にmainにマージしてください。