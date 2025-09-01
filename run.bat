@echo off
chcp 65001 >nul

echo 日経テスト過去問練習アプリを起動しています...

REM 仮想環境が存在するかチェック
if not exist "venv" (
    echo 仮想環境を作成しています...
    python -m venv venv
)

REM 仮想環境をアクティベート
echo 仮想環境をアクティベートしています...
call venv\Scripts\activate

REM 依存関係をインストール
echo 依存関係をインストールしています...
pip install -r requirements.txt

REM dataディレクトリが存在しない場合は作成
if not exist "data" (
    echo dataディレクトリを作成しています...
    mkdir data
)

REM アプリケーションを起動
echo アプリケーションを起動しています...
echo http://localhost:5000 でアクセスできます
echo 停止するにはCtrl+Cを押してください
echo -----------------------------------

python app.py

pause