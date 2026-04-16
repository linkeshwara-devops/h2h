# Harvest2Hotel

Harvest2Hotel is a B2B ecommerce marketplace built with Python Flask for hotel buyers and food manufacturers. It runs immediately with a local SQLite database and can also use MySQL.

## Features

- Modern floating glassmorphism UI
- Login and registration pages
- Hotel buyer product catalog with quantity-based cart
- Dedicated payment page and order confirmation flow
- Manufacturer dashboard for uploading products
- Manufacturer store pages
- Product detail pages with Flipkart/Amazon-style review cards
- Seed data for pulses, tomatoes, potatoes, rice, wheat, and spices

## Stack

- Python Flask
- SQLite by default
- MySQL via SQLAlchemy + PyMySQL when configured
- HTML, CSS, JavaScript

## Quick Start

1. Install packages:

```powershell
pip install -r requirements.txt
```

2. Run the server:

```powershell
python app.py
```

3. Open `http://127.0.0.1:5000`

## Optional MySQL Setup

If you want MySQL instead of the default local SQLite database:

1. Install the MySQL driver if needed:

```powershell
pip install pymysql
```

2. Create a MySQL database:

```sql
CREATE DATABASE harvest2hotel;
```

3. Set the database URL in PowerShell:

```powershell
$env:FLASK_SQLALCHEMY_DATABASE_URI="mysql+pymysql://root:password@localhost/harvest2hotel"
```

## Demo Accounts

- Buyer: `buyer@demo.com` / `demo123`
- Manufacturer: `raghav@greenpulse.com` / `demo123`

## Archive

The packaged project is created as `Harvest2Hotel.zip`.
