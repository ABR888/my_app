# app.py

from flask import Flask, request, jsonify
import sqlite3
import datetime
import uuid

app = Flask(__name__)
DATABASE = 'database.db'

def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
def init_db():
    with connect_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            wallet REAL DEFAULT 0.0
        )''')
        
        db.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL,
            description TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

init_db()

# Register
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data['name']
    phone = data['phone']
    password = data['password']
    
    try:
        with connect_db() as db:
            db.execute('INSERT INTO users (name, phone, password) VALUES (?, ?, ?)', (name, phone, password))
            db.commit()
        return jsonify({'message': 'User registered successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Phone number already registered'}), 400

# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data['phone']
    password = data['password']
    
    with connect_db() as db:
        user = db.execute('SELECT * FROM users WHERE phone = ? AND password = ?', (phone, password)).fetchone()
        if user:
            return jsonify({'message': 'Login successful', 'user_id': user['id']})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

# Get Wallet
@app.route('/wallet/<int:user_id>', methods=['GET'])
def wallet(user_id):
    with connect_db() as db:
        user = db.execute('SELECT wallet FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            return jsonify({'wallet': user['wallet']})
        else:
            return jsonify({'error': 'User not found'}), 404

# Buy Data (Mock)
@app.route('/buy_data', methods=['POST'])
def buy_data():
    data = request.get_json()
    user_id = data['user_id']
    amount = data['amount']
    description = data['description']
    
    with connect_db() as db:
        user = db.execute('SELECT wallet FROM users WHERE id = ?', (user_id,)).fetchone()
        if user and user['wallet'] >= amount:
            new_balance = user['wallet'] - amount
            db.execute('UPDATE users SET wallet = ? WHERE id = ?', (new_balance, user_id))
            db.execute('INSERT INTO transactions (user_id, type, amount, description, date) VALUES (?, ?, ?, ?, ?)', 
                       (user_id, 'buy_data', amount, description, datetime.datetime.now().isoformat()))
            db.commit()
            return jsonify({'message': 'Data purchased successfully', 'new_balance': new_balance})
        else:
            return jsonify({'error': 'Insufficient balance'}), 400

# Get Transactions
@app.route('/transactions/<int:user_id>', methods=['GET'])
def transactions(user_id):
    with connect_db() as db:
        txns = db.execute('SELECT * FROM transactions WHERE user_id = ?', (user_id,)).fetchall()
        return jsonify([dict(txn) for txn in txns])

if __name__ == '__main__':
    app.run(debug=True)

