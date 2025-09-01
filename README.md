# 日経テスト過去問練習アプリ

日本経済新聞社の日経経済知力テスト（日経TEST）の練習ができるWebアプリケーションです。

## 機能

- **4択クイズ**: 日経公式サンプル問題を参考にした本格的な問題
- **詳細解説**: 正解・不正解に関わらず、各問題の詳しい解説を表示
- **成績分析**: ダッシュボードで正答率やカテゴリ別成績を可視化
- **学習履歴**: 過去の回答結果を記録し、復習に活用可能
- **レスポンシブデザイン**: PC・スマートフォン両対応

## 日経TESTについて

日経テストは以下の5つの評価軸で構成されています：

1. **基礎知識**: 経済の基本的な用語や仕組み
2. **実践知識**: 最新の経済トピックやニュース
3. **視野の広さ**: 政治、国際情勢など幅広い知識
4. **知識を知恵にする力**: 情報を組み合わせて考える力
5. **知恵を活用する力**: 現実のビジネスに応用する力

## セットアップ

### 必要な環境
- Python 3.7以上
- pip

### インストール手順

1. リポジトリをクローン
```bash
git clone https://github.com/d01ki/nikkei-quiz.git
cd nikkei-quiz
```

2. 仮想環境を作成（推奨）
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

4. アプリケーションを起動
```bash
python app.py
```

5. ブラウザで http://localhost:5000 にアクセス

## 使い方

1. **ホーム画面**: アプリの概要と統計を確認
2. **クイズ開始**: ランダムに出題される問題に挑戦
3. **ダッシュボード**: 学習進捗と成績を可視化で確認

## ファイル構成

```
nikkei-quiz/
├── app.py              # メインアプリケーション
├── requirements.txt    # Python依存関係
├── data/
│   ├── questions.json  # 問題データ
│   └── user_stats.json # ユーザー統計（自動生成）
└── templates/
    ├── base.html       # ベーステンプレート
    ├── index.html      # ホーム画面
    ├── quiz.html       # クイズ画面
    └── dashboard.html  # ダッシュボード画面
```

## 問題データについて

現在のアプリには、日経新聞公式サイトのサンプル問題を参考にした10問が収録されています。

### 問題の追加方法

`data/questions.json` に以下の形式で問題を追加できます：

```json
{
  "id": "unique_id",
  "category": "基礎知識",
  "question": "問題文",
  "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
  "correct_answer": 0,
  "explanation": "詳細な解説",
  "difficulty": "中級",
  "source": "出典情報"
}
```

## 技術仕様

- **フロントエンド**: HTML5, CSS3, JavaScript (Vanilla)
- **バックエンド**: Python Flask
- **データ**: JSON形式でローカル保存
- **スタイル**: レスポンシブデザイン、CSS Grid/Flexbox
- **アイコン**: Font Awesome

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 注意事項

- このアプリは日経新聞社の非公式な練習アプリです
- 問題は日経公式サンプル問題を参考に作成されています
- 実際の日経テストとは内容や難易度が異なる場合があります

## 開発者

[@d01ki](https://github.com/d01ki)

## 貢献

プルリクエストやイシューの報告を歓迎します！

---

**日経テスト公式情報**: https://school.nikkei.co.jp/nn/special/ntest/