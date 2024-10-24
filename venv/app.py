from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import json
from epaycosdk.epayco import Epayco

load_dotenv()

app = Flask(__name__)

epayco = Epayco({
    "apiKey": os.getenv("PUBLIC_KEY"),
    "privateKey": os.getenv("PRIVATE_KEY"),
    "lenguage": "ES",
    "test": os.getenv("EPAYCO_TEST") == "True"
})

# Crear token de la tarjeta
def createToken(data):
    try:
        cardInfo = {
            "card[number]": data["card_number"],
            "card[exp_year]": data["exp_year"],
            "card[exp_month]": data["exp_month"],
            "card[cvc]": data["cvc"],
            "hasCvv": True
        }
        token = epayco.token.create(cardInfo)
        return token
    except Exception as e:
        return {"error": str(e)}

# Crear cliente
def createCustomer(token, data):
    customerInfo = {
        "name": data["name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "phone": data["phone"],
        "default": True
    }
    customerInfo["token_card"] = token
    try:
        customer = epayco.customer.create(customerInfo)
        return customer
    except Exception as e:
        return {"error": str(e)}

# Procesar pago
def processPayment(data, customer_id, token_card):
    try:
        paymentInfo = {
            "token_card": token_card,
            "customer_id": customer_id,
            "doc_type": "DNI",
            "doc_number": data["doc_number"],
            "name": data["name"],
            "last_name": data["last_name"],
            "email": data["email"],
            "city": data["city"],
            "address": data["address"],
            "phone": data["phone"],
            "cell_phone": data["cell_phone"],
            "bill": data["bill"],
            "description": "Pago servicio de transporte",
            "value": data["value"],
            "tax": 0,
            "tax_base": data["value"],
            "currency": "COP",
        }
        # Imprimir paymentInfo para depurar
        print("Payment Info: ", json.dumps(paymentInfo, indent=4))
        response = epayco.charge.create(paymentInfo)
        return response
    except Exception as e:
        return {"error": str(e)}

# Definición de endpoint
@app.route("/payment", methods=["POST"])
def payment():
    data = request.json
    
    # Crear token
    token_response = createToken(data)
    print("Token: ", json.dumps(token_response)) 
    
    # Verificar si se generó el token
    if token_response["status"] is False:
        return jsonify(token_response), 500
    
    tokenCard = token_response["id"]  # Id del token
    
    # Crear cliente
    customer_response = createCustomer(tokenCard, data)
    print("Customer: ", json.dumps(customer_response))
    
    # Verificar si se creó el cliente
    if "error" in customer_response:
        return jsonify(customer_response), 500
    
    customerId = customer_response["data"]["customerId"]  # Id del cliente
    
    # Procesar pago
    payment_response = processPayment(data, customerId, tokenCard)
    print("Payment: ", json.dumps(payment_response))
    
    # Verificar si se realizó el pago
    if "error" in payment_response:
        return jsonify(payment_response), 500
    
    return jsonify(payment_response), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)
