FROM python:3.9-slim

# ワーキングディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# dataディレクトリを作成
RUN mkdir -p data

# ポートを5000を公開
EXPOSE 5000

# アプリケーションを実行
CMD ["python", "app.py"]