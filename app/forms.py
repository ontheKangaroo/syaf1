from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from app.models import User, Post


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class PostForm(FlaskForm):
    body = TextAreaField('Say something', validators=[DataRequired()])
    image = FileField('Include an image', validators=[FileRequired()])
    anonymous = BooleanField('Make this post anonymous')
    submit = SubmitField('Submit')


class EditPostForm(FlaskForm):
    body = TextAreaField('Say something')
    image = FileField('Include an image')
    anonymous = BooleanField('Make this post anonymous')
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditCommentForm(FlaskForm):
    body = TextAreaField('Say something')
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    anonymous = BooleanField('Anonymous')
    style = SelectField('Style', choices=[('1', 'Impressionist'), ('2', 'Cubist'), ('3', 'Abstract')])
    # category = SelectField('Category', validators=[DataRequired()], choices=[(
    #     'Academic', 'Academic'), ('Art', 'Art')])
    submit = SubmitField('Submit')

    # def return_posts(self, anonymous):
    #     posts = Post.query.filter_by(anonymous=anonymous.data).first()
    #     return posts

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

