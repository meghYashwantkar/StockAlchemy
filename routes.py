from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
import logging
import json

from app import app, db
from models import User, Stock, Portfolio, Transaction
from forms import LoginForm, RegistrationForm, AddStockForm, SellStockForm, TransactionForm
from utils import get_stock_info, update_stock_data, calculate_portfolio_totals, get_portfolio_data_for_chart, update_average_buy_price

@app.route('/')
def index():
    """Homepage route"""
    return render_template('index.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        # Make the first user an admin
        if User.query.count() == 0:
            user.is_admin = True
            
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'danger')
            
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to requested page or dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    # Update stock prices
    update_stock_data()
    
    # Get portfolio data
    portfolio_items = Portfolio.query.filter_by(user_id=current_user.id).all()
    totals = calculate_portfolio_totals(current_user.id)
    
    # Create empty arrays for chart data (using only primitive types)
    labels = []
    values = []
    colors = []
    
    # Define colors as simple strings
    color_list = [
        '#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236',
        '#166a8f', '#00a950', '#58595b', '#8549ba', '#8b0000'
    ]
    
    # Process portfolio items safely
    if portfolio_items:
        for i, item in enumerate(portfolio_items):
            try:
                # Only include items with valid data
                if item.quantity > 0 and item.stock and item.stock.current_price:
                    # Use only primitive types (string, float)
                    symbol = str(item.stock.symbol)
                    value = float(item.quantity) * float(item.stock.current_price)
                    color = str(color_list[i % len(color_list)])
                    
                    # Add to our arrays
                    labels.append(symbol)
                    values.append(value)
                    colors.append(color)
            except Exception as e:
                print(f"Error processing portfolio item {i}: {e}")
    
    # Pre-convert to JSON strings
    chart_data = {
        'has_data': len(labels) > 0,
        'labels_json': json.dumps(labels),
        'values_json': json.dumps(values),
        'colors_json': json.dumps(colors)
    }
    
    # Recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html',
        title='Dashboard',
        portfolio=portfolio_items,
        totals=totals,
        chart_data=chart_data,
        recent_transactions=recent_transactions
    )

@app.route('/portfolio')
@login_required
def portfolio():
    """Portfolio management route"""
    # Update stock prices
    update_stock_data()
    
    # Get portfolio data
    portfolio_items = Portfolio.query.filter_by(user_id=current_user.id).all()
    totals = calculate_portfolio_totals(current_user.id)
    add_form = AddStockForm()
    
    return render_template(
        'portfolio.html',
        title='My Portfolio',
        portfolio=portfolio_items,
        totals=totals,
        add_form=add_form
    )

@app.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    """Add a stock to portfolio"""
    form = AddStockForm()
    
    if form.validate_on_submit():
        symbol = form.symbol.data.upper()
        quantity = form.quantity.data
        price = form.price.data
        
        # Check if stock exists in the database
        stock = Stock.query.filter_by(symbol=symbol).first()
        
        # If stock doesn't exist, fetch info and create it
        if not stock:
            stock_info = get_stock_info(symbol)
            if not stock_info:
                flash(f'Could not find stock with symbol {symbol}', 'danger')
                return redirect(url_for('portfolio'))
            
            stock = Stock(
                symbol=symbol,
                company_name=stock_info['company_name'],
                current_price=stock_info['current_price'],
                last_updated=datetime.utcnow()
            )
            db.session.add(stock)
            db.session.flush()  # Assign an ID without committing
        
        # Check if user already has this stock in portfolio
        portfolio = Portfolio.query.filter_by(user_id=current_user.id, stock_id=stock.id).first()
        
        if portfolio:
            # Calculate new average price and update quantity
            total_value = (portfolio.quantity * portfolio.average_buy_price) + (quantity * price)
            portfolio.quantity += quantity
            portfolio.average_buy_price = total_value / portfolio.quantity
        else:
            # Create new portfolio entry
            portfolio = Portfolio(
                user_id=current_user.id,
                stock_id=stock.id,
                quantity=quantity,
                average_buy_price=price
            )
            db.session.add(portfolio)
        
        # Record the transaction
        transaction = Transaction(
            user_id=current_user.id,
            stock_id=stock.id,
            transaction_type='BUY',
            quantity=quantity,
            price=price
        )
        db.session.add(transaction)
        
        try:
            db.session.commit()
            flash(f'Successfully added {quantity} shares of {symbol} to your portfolio', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding stock: {str(e)}', 'danger')
    
    return redirect(url_for('portfolio'))

@app.route('/sell_stock/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def sell_stock(stock_id):
    """Sell stock from portfolio"""
    portfolio = Portfolio.query.filter_by(user_id=current_user.id, stock_id=stock_id).first_or_404()
    stock = Stock.query.get_or_404(stock_id)
    form = SellStockForm()
    
    if form.validate_on_submit():
        quantity = form.quantity.data
        price = form.price.data
        
        if quantity > portfolio.quantity:
            flash('You cannot sell more shares than you own', 'danger')
            return redirect(url_for('portfolio'))
        
        # Update portfolio quantity
        portfolio.quantity -= quantity
        
        # Record the transaction
        transaction = Transaction(
            user_id=current_user.id,
            stock_id=stock.id,
            transaction_type='SELL',
            quantity=quantity,
            price=price
        )
        db.session.add(transaction)
        
        # If sold all shares, remove from portfolio
        if portfolio.quantity <= 0:
            db.session.delete(portfolio)
            
        try:
            db.session.commit()
            flash(f'Successfully sold {quantity} shares of {stock.symbol} at ${price:.2f} per share', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error selling stock: {str(e)}', 'danger')
            
        return redirect(url_for('portfolio'))
    
    # Pre-fill the form with current stock price
    if stock.current_price:
        form.price.data = stock.current_price
    
    return render_template(
        'sell_stock.html',
        title=f'Sell {stock.symbol}',
        form=form,
        stock=stock,
        portfolio=portfolio
    )

@app.route('/transactions')
@login_required
def transactions():
    """View transaction history"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(
        Transaction.timestamp.desc()
    ).paginate(page=page, per_page=per_page)
    
    form = TransactionForm()
    
    return render_template(
        'transactions.html',
        title='Transaction History',
        transactions=transactions,
        form=form
    )

@app.route('/admin')
@login_required
def admin():
    """Admin panel route"""
    if not current_user.is_admin:
        flash('You do not have permission to access the admin panel', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.username).all()
    stocks = Stock.query.order_by(Stock.symbol).all()
    recent_transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(20).all()
    
    return render_template(
        'admin.html',
        title='Admin Panel',
        users=users,
        stocks=stocks,
        transactions=recent_transactions
    )

@app.route('/admin/update_stocks')
@login_required
def admin_update_stocks():
    """Update all stock prices (admin only)"""
    if not current_user.is_admin:
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        update_stock_data()
        flash('Stock prices updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating stock prices: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/search_stock')
@login_required
def search_stock():
    """API endpoint to search for stock information"""
    symbol = request.args.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({'error': 'No symbol provided'}), 400
    
    stock_info = get_stock_info(symbol)
    
    if not stock_info:
        return jsonify({'error': f'Could not find stock with symbol {symbol}'}), 404
    
    return jsonify(stock_info)

@app.route('/record_transaction', methods=['GET', 'POST'])
@login_required
def record_transaction():
    """Record a manual transaction"""
    form = TransactionForm()
    
    if form.validate_on_submit():
        symbol = form.symbol.data.upper()
        transaction_type = form.transaction_type.data
        quantity = form.quantity.data
        price = form.price.data
        
        # Check if stock exists in the database
        stock = Stock.query.filter_by(symbol=symbol).first()
        
        # If stock doesn't exist, fetch info and create it
        if not stock:
            stock_info = get_stock_info(symbol)
            if not stock_info:
                flash(f'Could not find stock with symbol {symbol}', 'danger')
                return redirect(url_for('transactions'))
            
            stock = Stock(
                symbol=symbol,
                company_name=stock_info['company_name'],
                current_price=stock_info['current_price'],
                last_updated=datetime.utcnow()
            )
            db.session.add(stock)
            db.session.flush()  # Assign an ID without committing
        
        # Record the transaction
        transaction = Transaction(
            user_id=current_user.id,
            stock_id=stock.id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price
        )
        db.session.add(transaction)
        
        # Update portfolio based on transaction type
        portfolio = Portfolio.query.filter_by(user_id=current_user.id, stock_id=stock.id).first()
        
        if transaction_type == 'BUY':
            if portfolio:
                # Calculate new average price and update quantity for BUY
                total_value = (portfolio.quantity * portfolio.average_buy_price) + (quantity * price)
                portfolio.quantity += quantity
                portfolio.average_buy_price = total_value / portfolio.quantity
            else:
                # Create new portfolio entry
                portfolio = Portfolio(
                    user_id=current_user.id,
                    stock_id=stock.id,
                    quantity=quantity,
                    average_buy_price=price
                )
                db.session.add(portfolio)
        else:  # SELL
            if not portfolio or portfolio.quantity < quantity:
                flash('You cannot sell more shares than you own', 'danger')
                db.session.rollback()
                return redirect(url_for('transactions'))
            
            # Update portfolio quantity
            portfolio.quantity -= quantity
            
            # If sold all shares, remove from portfolio
            if portfolio.quantity <= 0:
                db.session.delete(portfolio)
        
        try:
            db.session.commit()
            flash(f'Transaction recorded: {transaction_type} {quantity} shares of {symbol} at ${price:.2f}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording transaction: {str(e)}', 'danger')
            
        return redirect(url_for('transactions'))
    
    return render_template(
        'record_transaction.html',
        title='Record Transaction',
        form=form
    )

@app.route('/sell_stock.html')
@login_required
def sell_stock_template():
    """Route for the sell stock template (will be loaded via AJAX)"""
    form = SellStockForm()
    stock_id = request.args.get('stock_id', 0, type=int)
    
    portfolio = Portfolio.query.filter_by(user_id=current_user.id, stock_id=stock_id).first_or_404()
    stock = Stock.query.get_or_404(stock_id)
    
    # Pre-fill the form with current stock price
    if stock.current_price:
        form.price.data = stock.current_price
    
    return render_template(
        'sell_stock.html',
        title=f'Sell {stock.symbol}',
        form=form,
        stock=stock,
        portfolio=portfolio
    )
