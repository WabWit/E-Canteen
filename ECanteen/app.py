from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson.decimal128 import Decimal128
import os


app = Flask(__name__)

uri = "mongodb+srv://wab:ZHxGMWcsVqDvVfDF@ecanteendb.plico.mongodb.net/?retryWrites=true&w=majority&appName=ECANTEENDB"
client = MongoClient(uri)

# MongoDB Atlas connection

db = client["ECanteenDB"]
accounts_collection = db["Accounts"]
sales_collection = db["Sales"]

def convert_decimal(doc):
    """Convert Decimal128 or int values to float for JSON serialization"""
    for key, value in doc.items():
        if isinstance(value, Decimal128):
            doc[key] = float(value.to_decimal())  # Convert Decimal128 to float
        elif isinstance(value, int):
            doc[key] = float(value)  # Convert int to float
    return doc

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/confirm_account', methods=['POST'])
def confirm_account():
    try:
        # Get form data
        account_id = request.form['account_id'].strip()
        total = int(request.form['total'])

        # Find account in MongoDB
        account = accounts_collection.find_one({"ID": account_id})
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        # Get balance (stored as an integer)
        balance = account['Balance']
        if balance < total:
            return jsonify({'error': 'Insufficient balance'}), 400

        # Return success if checks pass
        print("amogus" + account['AccountName'])
        return jsonify({'message': 'Account validated', 'account_name' : account['AccountName']}), 200
    

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/make_purchase', methods=['POST'])
def make_purchase():
    try:
        # Get form data
        account_id = request.form['account_id'].strip()
        cart = eval(request.form['cart'])  # In production, use proper JSON parsing
        total = int(request.form['total'])  # Ensure total is an integer
        purchaseTot = int(request.form['purchaseTotal'])

        # Find account in MongoDB
        account = accounts_collection.find_one({"ID": account_id})
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        # Get balance (stored as an integer)
        balance = account['Balance']
        if balance < total:
            return jsonify({'error': 'Insufficient balance'}), 400

        # Update sales for each item in cart
        for item in cart:
            category = item['category']
            price = int(item['price'])  # Ensure price is an integer
            sales_collection.update_one(
                {"Category": category},
                {"$inc": {"Total": price}},  # Increment by integer value
                upsert=True
            )

        # Update account balance
        new_balance = balance - total
        accounts_collection.update_one(
            {"ID": account_id},
            {"$set": {"Balance": new_balance}}
        )
        accounts_collection.update_one(
            {"ID": account_id},
            {"$inc": {"Purchases": purchaseTot}}
        )

        # Return success message with new balance
        return jsonify({
            'message': f'Purchase successful! New balance: Php {new_balance}',
            'new_balance': new_balance
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create indexes if they don't exist
    accounts_collection.create_index("ID", unique=True)
    sales_collection.create_index("Category", unique=True)
    app.run(debug=True)