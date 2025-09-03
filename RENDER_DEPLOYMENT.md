# Render デプロイメント設定

## 🚀 環境変数設定（必須）

Renderダッシュボードで以下の環境変数を設定してください：

```
DATABASE_URL=postgresql://user:password@hostname:port/database
SECRET_KEY=your-super-secret-key-change-this-in-production  
FLASK_ENV=production
```

## 📋 Build & Deploy Settings

- **Branch**: `feature/user-authentication`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Python Version**: 3.11.9

## 🔧 トラブルシューティング

### よくあるエラーと解決法

1. **psycopg2インストールエラー**
   - requirements.txt で `psycopg2-binary` を使用

2. **データベース接続エラー**
   - DATABASE_URL の形式を確認
   - PostgreSQLサービスが起動しているか確認

3. **秘密鍵エラー**
   - SECRET_KEY 環境変数が設定されているか確認

4. **Python版エラー**
   - runtime.txt で Python 3.11.9 を指定

## 🎯 デプロイ後の確認

- [ ] アプリが正常起動
- [ ] データベース接続成功
- [ ] ユーザー登録・ログイン動作
- [ ] 問題解答機能動作

## 📞 サポート

デプロイでエラーが出る場合は、Renderのビルドログを確認してください。