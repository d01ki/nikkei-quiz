# 🚀 デプロイメントガイド

このドキュメントでは、日経クイズ練習アプリをさまざまなプラットフォームにデプロイする方法を説明します。

## 📋 デプロイ準備（共通）

アプリには以下のデプロイ用ファイルが含まれています：
- `Procfile` - Heroku用プロセス定義
- `runtime.txt` - Python バージョン指定
- `requirements.txt` - 依存関係（gunicorn含む）
- `Dockerfile` - Docker用設定
- `docker-compose.yml` - Docker Compose設定

## 🟢 1. Heroku（推奨・最も簡単）

**特徴**: 無料枠、簡単デプロイ、自動HTTPS、スケーリング対応

### 手順:

1. **Herokuアカウント作成**
   - https://www.heroku.com/ でアカウント作成

2. **Heroku CLIインストール**
   ```bash
   # Windows
   https://devcenter.heroku.com/articles/heroku-cli からダウンロード
   
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Ubuntu/Debian
   sudo snap install --classic heroku
   ```

3. **デプロイ実行**
   ```bash
   # Herokuにログイン
   heroku login
   
   # プロジェクトディレクトリに移動
   cd nikkei-quiz
   
   # Herokuアプリ作成
   heroku create your-app-name
   
   # デプロイ
   git push heroku main
   
   # アプリを開く
   heroku open
   ```

4. **環境変数設定（オプション）**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set FLASK_ENV=production
   ```

**✅ URL**: `https://your-app-name.herokuapp.com`

---

## 🟡 2. Railway

**特徴**: モダン、簡単、GitHub連携、無料枠500時間/月

### 手順:

1. **https://railway.app** でアカウント作成
2. **GitHub連携** でリポジトリを選択
3. **自動デプロイ** が開始されます
4. **Environment Variables** で設定:
   - `SECRET_KEY` = `your-secret-key`
   - `FLASK_ENV` = `production`

**✅ URL**: `https://your-app-name.railway.app`

---

## 🟠 3. Render

**特徴**: 静的サイトホスティング、自動SSL、GitHub連携

### 手順:

1. **https://render.com** でアカウント作成
2. **New Web Service** を選択
3. **GitHubリポジトリ** を選択
4. **設定**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment Variables:
     - `SECRET_KEY` = `your-secret-key`
     - `FLASK_ENV` = `production`

**✅ URL**: `https://your-app-name.onrender.com`

---

## 🔵 4. Vercel

**特徴**: 高速、CDN、自動HTTPS、GitHub連携

### Vercelフォルダ作成:
```bash
mkdir .vercel
```

### vercel.json作成:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "./app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/"
    }
  ]
}
```

### 手順:
1. **https://vercel.com** でアカウント作成
2. **GitHub連携** でリポジトリをインポート
3. **自動デプロイ** が開始

**✅ URL**: `https://your-app-name.vercel.app`

---

## 🐳 5. Docker（自分のサーバー）

**特徴**: 完全制御、どこでも動作、コンテナ化

### 手順:

```bash
# Dockerイメージビルド
docker build -t nikkei-quiz .

# コンテナ実行
docker run -p 5000:5000 nikkei-quiz

# または Docker Compose使用
docker-compose up -d
```

**✅ URL**: `http://your-server:5000`

---

## ☁️ 6. AWS/GCP/Azure

### AWS Elastic Beanstalk:
```bash
pip install awsebcli
eb init
eb create production
eb deploy
```

### Google Cloud Run:
```bash
gcloud run deploy nikkei-quiz \
  --source . \
  --platform managed \
  --region us-central1
```

### Azure Container Instances:
```bash
az container create \
  --resource-group myResourceGroup \
  --name nikkei-quiz \
  --image nikkei-quiz \
  --ports 5000
```

---

## 🛠️ デプロイ後の設定

### 環境変数（本番環境）:
- `SECRET_KEY`: セキュアな秘密鍵
- `FLASK_ENV`: `production`
- `PORT`: ポート番号（通常は自動設定）

### データ永続化:
- 本番環境では PostgreSQL や MongoDB などのデータベース使用を推奨
- 現在はJSONファイル保存（開発用）

### HTTPS設定:
- ほとんどのプラットフォームで自動設定
- 独自ドメイン使用可能

### モニタリング:
- ログ監視
- パフォーマンス監視
- エラー追跡

---

## 📊 比較表

| プラットフォーム | 難易度 | 無料枠 | 自動SSL | スケーリング | 推奨度 |
|---------------|-------|-------|---------|------------|-------|
| Heroku        | ⭐     | ✅     | ✅       | ✅          | 🌟🌟🌟🌟🌟 |
| Railway       | ⭐     | ✅     | ✅       | ✅          | 🌟🌟🌟🌟   |
| Render        | ⭐⭐    | ✅     | ✅       | ✅          | 🌟🌟🌟🌟   |
| Vercel        | ⭐⭐    | ✅     | ✅       | ✅          | 🌟🌟🌟    |
| Docker        | ⭐⭐⭐   | 📊     | 📊       | 📊          | 🌟🌟🌟    |
| AWS/GCP       | ⭐⭐⭐⭐  | 📊     | 📊       | ✅          | 🌟🌟     |

## 🎯 推奨デプロイ方法

### 🥇 初心者・テスト用: **Heroku**
- 最も簡単
- 豊富なドキュメント
- 一行でデプロイ可能

### 🥈 中級者用: **Railway / Render**
- モダンなUI
- 高速デプロイ
- 良い無料枠

### 🥉 上級者用: **AWS/GCP + Docker**
- 完全制御
- エンタープライズ対応
- スケーラブル

---

## ❓ トラブルシューティング

### よくある問題:

1. **Port エラー**
   ```python
   port = int(os.environ.get('PORT', 5000))
   ```

2. **静的ファイル 404**
   - `static/` フォルダがない場合の問題
   - CSSやJSはHTMLに埋め込み済み

3. **データ保存エラー**
   - 書き込み権限の問題
   - データベース使用を推奨

### デバッグ方法:
```bash
# ログ確認（Heroku）
heroku logs --tail

# 本番環境テスト
FLASK_ENV=production python app.py
```

---

**🎉 デプロイ成功後は、アプリのURLをシェアして多くの人に使ってもらいましょう！**