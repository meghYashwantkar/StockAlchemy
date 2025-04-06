from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Form for new user registration"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Validate username is unique"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate email is unique"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class AddStockForm(FlaskForm):
    """Form for adding a stock to portfolio"""
    symbol = StringField('Stock Symbol', validators=[DataRequired(), Length(min=1, max=10)])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    price = FloatField('Purchase Price Per Share', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Add Stock')

class SellStockForm(FlaskForm):
    """Form for selling stock from portfolio"""
    quantity = FloatField('Quantity to Sell', validators=[DataRequired(), NumberRange(min=0.01)])
    price = FloatField('Selling Price Per Share', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Sell Stock')

class TransactionForm(FlaskForm):
    """Form for recording a new transaction"""
    symbol = StringField('Stock Symbol', validators=[DataRequired(), Length(min=1, max=10)])
    transaction_type = SelectField('Transaction Type', choices=[('BUY', 'Buy'), ('SELL', 'Sell')], validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    price = FloatField('Price Per Share', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Record Transaction')
