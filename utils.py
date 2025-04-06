import yfinance as yf
import logging
from datetime import datetime, timedelta
from models import Stock, Portfolio
from app import db

def get_stock_info(symbol):
    """
    Get stock information from Yahoo Finance API
    Returns a dict with company name and current price
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Extract the relevant information
        company_name = info.get('longName', info.get('shortName', 'Unknown'))
        current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        
        return {
            'symbol': symbol.upper(),
            'company_name': company_name,
            'current_price': current_price
        }
    except Exception as e:
        logging.error(f"Error fetching stock info for {symbol}: {str(e)}")
        return None

def update_stock_data():
    """Update all stock prices in the database"""
    stocks = Stock.query.all()
    update_count = 0
    
    for stock in stocks:
        # Only update stocks that haven't been updated in the last hour
        if not stock.last_updated or (datetime.utcnow() - stock.last_updated) > timedelta(hours=1):
            stock_info = get_stock_info(stock.symbol)
            if stock_info and stock_info.get('current_price'):
                stock.current_price = stock_info.get('current_price')
                stock.last_updated = datetime.utcnow()
                update_count += 1
            
    if update_count > 0:
        try:
            db.session.commit()
            logging.info(f"Updated prices for {update_count} stocks")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating stock prices: {str(e)}")

def calculate_portfolio_totals(user_id):
    """Calculate total portfolio value and metrics for a user"""
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    
    total_current_value = 0.0
    total_investment = 0.0
    
    for position in portfolios:
        # Calculate values directly instead of using properties
        current_value = position.quantity * position.stock.current_price if position.stock.current_price else 0
        investment = position.quantity * position.average_buy_price if position.average_buy_price else 0
        
        total_current_value += float(current_value)
        total_investment += float(investment)
    
    total_profit_loss = float(total_current_value - total_investment)
    
    if total_investment > 0:
        profit_loss_percentage = float((total_profit_loss / total_investment) * 100)
    else:
        profit_loss_percentage = 0.0
    
    return {
        'total_current_value': total_current_value,
        'total_investment': total_investment,
        'total_profit_loss': total_profit_loss,
        'profit_loss_percentage': profit_loss_percentage
    }

def get_portfolio_data_for_chart(user_id):
    """Get portfolio data formatted for chart visualization"""
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    
    # Prepare data for pie chart
    labels = []
    values = []
    colors = []
    
    # List of distinct colors for the chart
    color_palette = [
        '#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236',
        '#166a8f', '#00a950', '#58595b', '#8549ba', '#8b0000',
        '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4'
    ]
    
    # Get portfolio data
    for i, position in enumerate(portfolios):
        # Skip positions with no quantity or price
        if (not position.quantity or position.quantity <= 0 or 
            not position.stock or not position.stock.current_price):
            continue
            
        try:
            # Calculate value manually to avoid property methods
            quantity = float(position.quantity)
            price = float(position.stock.current_price)
            value = quantity * price
            
            labels.append(str(position.stock.symbol))
            values.append(float(value))
            colors.append(str(color_palette[i % len(color_palette)]))
        except Exception as e:
            # Log error but continue with other positions
            print(f"Error processing portfolio position: {str(e)}")
            continue
    
    # Return simple Python primitives
    return {
        'labels': labels,
        'values': values,
        'colors': colors
    }

def update_average_buy_price(portfolio):
    """Recalculate the average buy price for a portfolio position"""
    from models import Transaction
    
    buy_transactions = Transaction.query.filter_by(
        user_id=portfolio.user_id,
        stock_id=portfolio.stock_id,
        transaction_type='BUY'
    ).all()
    
    total_shares = 0
    total_cost = 0
    
    for transaction in buy_transactions:
        total_cost += transaction.price * transaction.quantity
        total_shares += transaction.quantity
    
    if total_shares > 0:
        portfolio.average_buy_price = total_cost / total_shares
    else:
        portfolio.average_buy_price = 0
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating average buy price: {str(e)}")
