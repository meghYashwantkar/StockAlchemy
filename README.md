# Stock Alchemy

A modern web application for tracking and managing your stock portfolio investments.

## Overview

Stock Alchemy helps investors track their stock portfolios with real-time market data, performance metrics, and transaction history. Get insights into your investment performance with visual charts and detailed analytics.

## Features

- **User Authentication**: Secure account creation and login
- **Portfolio Management**: Add, view, and manage your stock holdings
- **Real-time Stock Data**: Automatic price updates via Yahoo Finance API
- **Transaction Tracking**: Record buy/sell transactions with complete history
- **Performance Metrics**: Track profit/loss and ROI for individual stocks and overall portfolio
- **Data Visualization**: Visual breakdowns of portfolio allocation and performance
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Admin Panel**: Administrative features for system management

## Tech Stack

- **Backend**: Python with Flask framework
- **Database**: SQLAlchemy ORM with SQLite (configurable for other databases)
- **Market Data**: Yahoo Finance API integration
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login
- **Visualization**: Chart.js

## Installation

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/meghYashwantkar/StockAlchemy.git
   cd stockAlchemy
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv env
   # On Windows
   env\Scripts\activate
   # On macOS/Linux
   source env/bin/activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables (optional)
   ```bash
   # On Windows
   set DATABASE_URL=sqlite:///portfolio.db
   set SESSION_SECRET=your_secret_key_here
   
   # On macOS/Linux
   export DATABASE_URL=sqlite:///portfolio.db
   export SESSION_SECRET=your_secret_key_here
   ```

5. Initialize the database
   ```bash
   flask run
   ```
   The application will automatically create the necessary database tables on first run.

## Usage

1. Start the Flask development server
   ```bash
   flask run
   ```

2. Access the application in your web browser at `http://127.0.0.1:5000`

3. Register a new account or log in

4. Add stocks to your portfolio by providing the ticker symbol, quantity, and purchase price

5. View your portfolio performance on the dashboard

## Admin Access

The first user to register on the system is automatically assigned admin privileges.

Admin users can:
- View all users in the system
- Manage stock data
- View system-wide transaction history

## License

[MIT License](LICENSE)

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Yahoo Finance API](https://pypi.org/project/yfinance/)
- [Chart.js](https://www.chartjs.org/)
- [Bootstrap](https://getbootstrap.com/) 