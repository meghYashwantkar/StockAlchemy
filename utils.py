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
    if not symbol:
        logging.error("Empty symbol provided to get_stock_info")
        return None
        
    try:
        print(f"Fetching stock info for {symbol}")
        stock = yf.Ticker(symbol)
        
        # Try to get price information
        try:
            # First try to get price directly from ticker
            current_price = stock.info.get('regularMarketPrice')
            if not current_price or current_price == 0:
                current_price = stock.info.get('currentPrice')
            
            # If that fails, try getting recent history
            if not current_price or current_price == 0:
                hist = stock.history(period="1d")
                if not hist.empty and 'Close' in hist.columns:
                    current_price = float(hist['Close'].iloc[-1])
                    
            # Default fallback
            if not current_price or current_price == 0:
                print(f"Warning: Could not get price for {symbol}, using default")
                current_price = 0.0
                
            # Get company name
            company_name = stock.info.get('longName') 
            if not company_name:
                company_name = stock.info.get('shortName', symbol.upper())
            
            print(f"Successfully retrieved {symbol} data: {company_name}, ${current_price}")
            
            return {
                'symbol': symbol.upper(),
                'company_name': company_name,
                'current_price': float(current_price)
            }
        except Exception as e:
            logging.error(f"Error getting price for {symbol}: {str(e)}")
            return {
                'symbol': symbol.upper(),
                'company_name': symbol.upper() + ' Inc.',
                'current_price': 0.0
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
    # Get portfolios with proper joining to ensure stock data is available
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    
    # Debug information
    print(f"Found {len(portfolios)} portfolio positions for user {user_id}")
    
    # Prepare data structures with primitives only
    chart_data = {
        'labels': [],
        'values': [],
        'colors': []
    }
    
    # Color list (pure strings)
    colors = [
        '#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236',
        '#166a8f', '#00a950', '#58595b', '#8549ba', '#8b0000', 
        '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4'
    ]
    
    # Check if portfolio is empty
    if not portfolios:
        print("Portfolio is empty, returning empty chart data")
        return chart_data
    
    # Process each portfolio position
    for i, position in enumerate(portfolios):
        try:
            # Skip invalid data
            if not position.quantity or position.quantity <= 0:
                print(f"Skipping position with invalid quantity: {position.quantity}")
                continue
            
            # Ensure stock exists and has a price
            if not position.stock:
                print(f"Skipping position with missing stock data")
                continue
                
            if not position.stock.current_price or position.stock.current_price <= 0:
                print(f"Stock {position.stock.symbol} has invalid price: {position.stock.current_price}")
                # Try to update the stock price
                stock_info = get_stock_info(position.stock.symbol)
                if stock_info and stock_info.get('current_price', 0) > 0:
                    position.stock.current_price = stock_info['current_price']
                    position.stock.last_updated = datetime.utcnow()
                    try:
                        db.session.commit()
                        print(f"Updated price for {position.stock.symbol} to {position.stock.current_price}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Failed to update price: {e}")
                else:
                    print(f"Could not get valid price for {position.stock.symbol}")
                    continue
            
            # Compute value as a primitive float
            quantity = float(position.quantity)
            price = float(position.stock.current_price)
            value = quantity * price
            
            # Only use primitive strings and floats
            symbol = str(position.stock.symbol)
            color_index = i % len(colors)
            
            # Add primitives to the result
            chart_data['labels'].append(symbol)
            chart_data['values'].append(value)
            chart_data['colors'].append(colors[color_index])
            
            print(f"Added position to chart: {symbol}, value: {value}")
            
        except Exception as e:
            print(f"Error processing portfolio position: {e}")
            continue
    
    print(f"Final chart data: {len(chart_data['labels'])} stocks, values: {chart_data['values']}")
    return chart_data

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
