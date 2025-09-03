# Render デプロイメント設定

## 🚀 環境変数設定（必須）

Renderダッシュボードで以下の環境変数を設定してください：

```
DATABASE_URL=postgresql://user:password@hostname:port/database
SECRET_KEY=your-super-secret-key-change-this-in-production  
FLASK_ENV=production
```

## 📋 Build & Deploy Settings

- **Branch**: `main`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Python Version**: 3.11.9

## 🔧 PostgreSQL設定のポイント

### 1. データベースドライバー
- **psycopg2-binary**を使用（pg8000から変更）
- RenderのPostgreSQLとの互換性が向上

### 2. URL変換の最適化
- `postgres://` → `postgresql://` のシンプルな変換
- 複雑なドライバー指定を削除

### 3. 接続プール設定
- Render環境に最適化されたプール設定
- タイムアウト処理の強化

## 🔧 トラブルシューティング

### よくあるエラーと解決法

1. **PostgreSQL接続エラー**
   - DATABASE_URL の形式を確認（`postgresql://`で始まる）
   - PostgreSQLサービスが起動しているか確認
   - Renderのデータベース設定を確認

2. **psycopg2インストールエラー**
   - requirements.txt で `psycopg2-binary` を使用
   - `pg8000`は削除済み

3. **秘密鍵エラー**
   - SECRET_KEY 環境変数が設定されているか確認
   - 本番環境では必ず変更すること

4. **Python版エラー**
   - runtime.txt で Python 3.11.9 を指定

## 🎯 デプロイ後の確認

- [ ] アプリが正常起動
- [ ] `/health` エンドポイントでデータベース接続確認
- [ ] ユーザー登録・ログイン動作
- [ ] 問題解答機能動作
- [ ] 統計データの永続化

## 📊 ヘルスチェック

デプロイ後は以下のURLでアプリの状態を確認できます：
```
https://your-app-name.onrender.com/health
```

正常な場合のレスポンス例：
```json
{
  "status": "healthy",
  "database": "connected", 
  "database_type": "PostgreSQL (psycopg2)",
  "db_initialized": true
}
```

## 📞 サポート

デプロイでエラーが出る場合は、Renderのビルドログを確認してください。
データベース接続問題の場合は、まず `/health` エンドポイントを確認してください。
