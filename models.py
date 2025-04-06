from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model for authentication and profile"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set user password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check if provided password matches stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Stock(db.Model):
    """Stock model for tracking individual stocks"""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, index=True)
    company_name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='stock', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='stock', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'

class Portfolio(db.Model):
    """Portfolio model for linking users to their stock holdings"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    quantity = db.Column(db.Float, default=0)
    average_buy_price = db.Column(db.Float, nullable=True)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'stock_id', name='_user_stock_uc'),)
    
    @property
    def current_value(self):
        """Calculate current value of this position"""
        if self.stock.current_price:
            return self.quantity * self.stock.current_price
        return 0
    
    @property
    def initial_investment(self):
        """Calculate initial investment amount"""
        if self.average_buy_price:
            return self.quantity * self.average_buy_price
        return 0
    
    @property
    def profit_loss(self):
        """Calculate profit/loss for this position"""
        if self.average_buy_price and self.stock.current_price:
            return self.current_value - self.initial_investment
        return 0
    
    @property
    def profit_loss_percentage(self):
        """Calculate profit/loss percentage"""
        if self.initial_investment and self.initial_investment > 0:
            return (self.profit_loss / self.initial_investment) * 100
        return 0
    
    def __repr__(self):
        return f'<Portfolio {self.user_id} - {self.stock.symbol if self.stock else "Unknown"}>'

class Transaction(db.Model):
    """Transaction model for recording buy/sell activities"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    transaction_type = db.Column(db.String(4), nullable=False)  # BUY or SELL
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def transaction_value(self):
        """Calculate total value of transaction"""
        return self.quantity * self.price
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.stock.symbol if self.stock else "Unknown"} - {self.quantity}>'
