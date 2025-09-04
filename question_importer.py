import os
import json
import re
from datetime import datetime
from PIL import Image
import pytesseract
import openai
from typing import List, Dict, Any, Optional

class QuestionImageProcessor:
    """画像から問題を抽出・処理するクラス"""
    
    def __init__(self):
        # OpenAI APIキーを環境変数から取得
        self.openai_client = openai.OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY', '')
        )
        
        # Tesseractの設定（日本語対応）
        self.tesseract_config = '--lang jpn+eng -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ。、？！（）「」[]：；・'
    
    def extract_text_from_image(self, image_path: str) -> str:
        """画像からテキストを抽出"""
        try:
            # 画像を開く
            image = Image.open(image_path)
            
            # 画像の前処理（必要に応じて）
            image = self.preprocess_image(image)
            
            # OCRでテキスト抽出
            extracted_text = pytesseract.image_to_string(
                image, 
                config=self.tesseract_config
            )
            
            print(f"✅ 画像からテキスト抽出完了: {len(extracted_text)}文字")
            print(f"抽出されたテキストプレビュー: {extracted_text[:200]}...")
            
            return extracted_text.strip()
            
        except Exception as e:
            print(f"❌ 画像からのテキスト抽出に失敗: {e}")
            return ""
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """画像の前処理（OCR精度向上のため）"""
        try:
            # グレースケール変換
            if image.mode != 'L':
                image = image.convert('L')
            
            # 画像サイズが小さすぎる場合はリサイズ
            width, height = image.size
            if width < 800 or height < 600:
                # アスペクト比を維持してリサイズ
                aspect_ratio = width / height
                new_height = 1200
                new_width = int(new_height * aspect_ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            print(f"⚠️ 画像前処理でエラー: {e}")
            return image
    
    def parse_question_with_ai(self, extracted_text: str) -> Optional[Dict[str, Any]]:
        """AIを使って抽出したテキストから問題データを構造化"""
        try:
            if not self.openai_client.api_key:
                print("⚠️ OpenAI APIキーが設定されていません")
                return None
            
            prompt = f"""
以下の日経テスト問題のテキストから、JSON形式で問題データを抽出してください。

抽出されたテキスト:
{extracted_text}

以下のJSON形式で回答してください:
{{
    "question": "問題文",
    "options": [
        "選択肢1",
        "選択肢2", 
        "選択肢3",
        "選択肢4"
    ],
    "correct_answer": 0,
    "explanation": "解説文",
    "category": "基礎知識|実践知識|視野の広さ|知識を知恵にする力|知恵を活用する力のいずれか",
    "difficulty": "初級|中級|上級のいずれか",
    "source": "日経TEST公式テキスト&問題集 2024-25年版"
}}

注意事項:
- correct_answerは0-3の数値（0=最初の選択肢）
- optionsは必ず4つの選択肢
- categoryは日経TESTの5つのカテゴリから選択
- 解説が不明な場合は空文字列
- JSONのみを回答し、他の説明は不要
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは日経テストの問題を正確に構造化する専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # レスポンスからJSONを抽出
            content = response.choices[0].message.content.strip()
            
            # JSONを抽出（```json から ``` の間を探す）
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # ```で囲まれていない場合は全体をJSONとして扱う
                json_str = content
            
            try:
                question_data = json.loads(json_str)
                
                # データ検証
                if self.validate_question_data(question_data):
                    print("✅ AIによる問題データ構造化完了")
                    return question_data
                else:
                    print("❌ 問題データの検証に失敗")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析エラー: {e}")
                print(f"レスポンス内容: {content}")
                return None
                
        except Exception as e:
            print(f"❌ AI問題解析に失敗: {e}")
            return None
    
    def validate_question_data(self, data: Dict[str, Any]) -> bool:
        """問題データの妥当性を検証"""
        try:
            # 必須フィールドの存在確認
            required_fields = ['question', 'options', 'correct_answer', 'category']
            for field in required_fields:
                if field not in data:
                    print(f"❌ 必須フィールド '{field}' がありません")
                    return False
            
            # 選択肢の数を確認
            if not isinstance(data['options'], list) or len(data['options']) != 4:
                print("❌ 選択肢は4つ必要です")
                return False
            
            # 正解番号の確認
            if not isinstance(data['correct_answer'], int) or not (0 <= data['correct_answer'] <= 3):
                print("❌ 正解番号は0-3の範囲内である必要があります")
                return False
            
            # カテゴリの確認
            valid_categories = [
                '基礎知識', '実践知識', '視野の広さ', 
                '知識を知恵にする力', '知恵を活用する力'
            ]
            if data['category'] not in valid_categories:
                print(f"❌ 無効なカテゴリ: {data['category']}")
                return False
            
            print("✅ 問題データの検証成功")
            return True
            
        except Exception as e:
            print(f"❌ データ検証エラー: {e}")
            return False
    
    def process_image_to_question(self, image_path: str) -> Optional[Dict[str, Any]]:
        """画像から問題データを完全に処理"""
        try:
            print(f"📸 画像処理開始: {image_path}")
            
            # 1. 画像からテキストを抽出
            extracted_text = self.extract_text_from_image(image_path)
            if not extracted_text:
                print("❌ テキスト抽出に失敗")
                return None
            
            # 2. AIで問題データを構造化
            question_data = self.parse_question_with_ai(extracted_text)
            if not question_data:
                print("❌ 問題データの構造化に失敗")
                return None
            
            # 3. 一意のIDを生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            question_data['id'] = f"imported_{timestamp}"
            
            print("🎉 画像から問題データの作成完了!")
            return question_data
            
        except Exception as e:
            print(f"❌ 画像処理で予期しないエラー: {e}")
            return None

class QuestionManager:
    """問題データの管理クラス"""
    
    def __init__(self, questions_file: str = 'data/questions.json'):
        self.questions_file = questions_file
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """dataディレクトリが存在することを確認"""
        os.makedirs('data', exist_ok=True)
    
    def load_questions(self) -> List[Dict[str, Any]]:
        """既存の問題データを読み込み"""
        try:
            if os.path.exists(self.questions_file):
                with open(self.questions_file, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                    print(f"✅ 既存問題データ読み込み: {len(questions)}問")
                    return questions
            else:
                print("⚠️ 問題ファイルが存在しないため、新規作成します")
                return []
        except Exception as e:
            print(f"❌ 問題データ読み込みエラー: {e}")
            return []
    
    def save_questions(self, questions: List[Dict[str, Any]]) -> bool:
        """問題データを保存"""
        try:
            with open(self.questions_file, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            print(f"✅ 問題データ保存完了: {len(questions)}問")
            return True
        except Exception as e:
            print(f"❌ 問題データ保存エラー: {e}")
            return False
    
    def add_question(self, question_data: Dict[str, Any]) -> bool:
        """新しい問題を追加"""
        try:
            questions = self.load_questions()
            
            # 重複チェック（IDが同じものがないか）
            existing_ids = {q.get('id', '') for q in questions}
            if question_data.get('id', '') in existing_ids:
                print(f"⚠️ 問題ID '{question_data['id']}' は既に存在します")
                return False
            
            questions.append(question_data)
            return self.save_questions(questions)
            
        except Exception as e:
            print(f"❌ 問題追加エラー: {e}")
            return False
    
    def get_questions_stats(self) -> Dict[str, Any]:
        """問題統計を取得"""
        questions = self.load_questions()
        
        categories = {}
        difficulties = {}
        
        for q in questions:
            # カテゴリ別集計
            category = q.get('category', '不明')
            categories[category] = categories.get(category, 0) + 1
            
            # 難易度別集計
            difficulty = q.get('difficulty', '不明')
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
        
        return {
            'total': len(questions),
            'categories': categories,
            'difficulties': difficulties
        }