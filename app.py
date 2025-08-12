from flask import Flask, request, jsonify
import os

app = Flask(__name__)

def financial_transactions_to_sheet_array(json_data):
    header = [
        "id", "value", "balance", "type", "date",
        "description", "paymentId", "splitId"
    ]
    result = [header]
    for item in json_data:
        row = [
            item.get("id", ""),
            item.get("value", ""),
            item.get("balance", ""),
            item.get("type", ""),
            item.get("date", ""),
            item.get("description", ""),
            item.get("paymentId", ""),
            item.get("splitId", "")
        ]
        result.append(row)
    return result

@app.route('/extrato', methods=['POST'])
def extrato():
    json_data = request.json
    if not json_data:
        return jsonify({"error": "Nenhum JSON enviado"}), 400

    sheet_data = financial_transactions_to_sheet_array(json_data)
    print(sheet_data)  # Pra debug no logs do Render

    return jsonify({
        "status": "sucesso",
        "linhas": len(sheet_data) - 1
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
