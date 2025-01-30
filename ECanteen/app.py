from flask import Flask, render_template, request, jsonify
import pandas as pd
from pathlib import Path

app = Flask(__name__)
DATABASE_PATH = Path("database.xlsx")

def load_database():
    if DATABASE_PATH.exists():
        with pd.ExcelFile(DATABASE_PATH) as excel:
            accounts = pd.read_excel(excel, "Accounts", dtype={'ID': str})
            sales = pd.read_excel(excel, "Sales")
        return accounts, sales
    return pd.DataFrame(columns=["ID", "Account name", "Balance"]), pd.DataFrame(columns=["Category", "Total"])

def save_database(accounts, sales):
    with pd.ExcelWriter(DATABASE_PATH) as writer:
        accounts.to_excel(writer, "Accounts", index=False)
        sales.to_excel(writer, "Sales", index=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/make_purchase', methods=['POST'])
def make_purchase():
    try:
        data = request.form
        account_id = data['account_id'].strip()
        cart = eval(data['cart'])
        total = int(data['total'])

        accounts, sales = load_database()
        account_index = accounts.index[accounts['ID'] == account_id].tolist()
        
        if not account_index:
            return jsonify({'error': 'Account not found'}), 404
            
        index = account_index[0]
        balance = int(accounts.at[index, 'Balance'])
        
        if balance < total:
            return jsonify({'error': 'Insufficient balance'}), 400

        # Update sales
        for item in cart:
            category = item['category']
            price = item['price']
            if sales.empty or category not in sales['Category'].values:
                sales = sales._append({'Category': category, 'Total': price}, ignore_index=True)
            else:
                sales.loc[sales['Category'] == category, 'Total'] += price

        # Update balance
        new_balance = balance - total
        accounts.at[index, 'Balance'] = new_balance
        save_database(accounts, sales)
        
        return jsonify({
            'message': f'Purchase successful! New balance: Php {new_balance}',
            'new_balance': new_balance
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not DATABASE_PATH.exists():
        save_database(
            pd.DataFrame(columns=["ID", "Account name", "Balance"]),
            pd.DataFrame(columns=["Category", "Total"])
        )
    app.run(debug=True)