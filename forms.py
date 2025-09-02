from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    """ログインフォーム"""
    username = StringField('ユーザー名またはメールアドレス', 
                          validators=[DataRequired(message='ユーザー名またはメールアドレスを入力してください')])
    password = PasswordField('パスワード', 
                           validators=[DataRequired(message='パスワードを入力してください')])
    remember_me = BooleanField('ログイン状態を保持する')
    submit = SubmitField('ログイン')

class RegisterForm(FlaskForm):
    """ユーザー登録フォーム"""
    username = StringField('ユーザー名', 
                          validators=[
                              DataRequired(message='ユーザー名を入力してください'),
                              Length(min=3, max=20, message='ユーザー名は3文字以上20文字以下で入力してください')
                          ])
    email = StringField('メールアドレス', 
                       validators=[
                           DataRequired(message='メールアドレスを入力してください'),
                           Email(message='正しいメールアドレスを入力してください')
                       ])
    display_name = StringField('表示名（任意）', 
                             validators=[Length(max=50, message='表示名は50文字以下で入力してください')])
    password = PasswordField('パスワード', 
                           validators=[
                               DataRequired(message='パスワードを入力してください'),
                               Length(min=6, message='パスワードは6文字以上で入力してください')
                           ])
    password2 = PasswordField('パスワード確認', 
                            validators=[
                                DataRequired(message='パスワード確認を入力してください'),
                                EqualTo('password', message='パスワードが一致しません')
                            ])
    submit = SubmitField('登録')
    
    def validate_username(self, username):
        """ユーザー名の重複チェック"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('このユーザー名は既に使用されています。別のユーザー名を選択してください。')
    
    def validate_email(self, email):
        """メールアドレスの重複チェック"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('このメールアドレスは既に登録されています。')