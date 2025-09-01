#!/bin/bash

# 日経テスト過去問練習アプリ起動スクリプト

echo "日経テスト過去問練習アプリを起動しています..."

# 仮想環境が存在するかチェック
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
echo "仮想環境をアクティベートしています..."
source venv/bin/activate

# 依存関係をインストール
echo "依存関係をインストールしています..."
pip install -r requirements.txt

# dataディレクトリが存在しない場合は作成
if [ ! -d "data" ]; then
    echo "dataディレクトリを作成しています..."
    mkdir data
fi

# アプリケーションを起動
echo "アプリケーションを起動しています..."
echo "http://localhost:5000 でアクセスできます"
echo "停止するにはCtrl+Cを押してください"
echo "-----------------------------------"

python app.py