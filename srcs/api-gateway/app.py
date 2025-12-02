import os
import requests
import pika
import json
import logging
from flask import Flask, request, jsonify, Response

# Initialize Flask app
app = Flask(__name__)

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Environment Configuration ---
INVENTORY_VM_IP = os.environ.get('INVENTORY_VM_IP', '192.168.56.11')
INVENTORY_API_PORT = os.environ.get('INVENTORY_API_PORT', 8080)
INVENTORY_API_URL = f'http://{INVENTORY_VM_IP}:{INVENTORY_API_PORT}'

BILLING_VM_IP = os.environ.get('BILLING_VM_IP', '192.168.56.12')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'rabbitmq_user')
RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'rabbitmq_password')
RABBITMQ_VHOST = os.environ.get('RABBITMQ_VHOST', 'billing_vhost')
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE', 'billing_queue')

# --- Inventory Service Routing ---

@app.route('/api/movies', defaults={'path': ''}, methods=['GET', 'POST', 'DELETE'])
@app.route('/api/movies/<path:path>', methods=['GET', 'PUT', 'DELETE'])
def proxy_inventory(path):
    """
    Forwards requests to the Inventory service.
    """
    if path:
        url = f'{INVENTORY_API_URL}/api/movies/{path}'
    else:
        url = f'{INVENTORY_API_URL}/api/movies'
    
    logging.info(f"Proxying request: {request.method} {url}")
    
    try:
        if request.method == 'GET':
            resp = requests.get(url, params=request.args)
        elif request.method == 'POST':
            resp = requests.post(url, json=request.get_json())
        elif request.method == 'PUT':
            resp = requests.put(url, json=request.get_json())
        elif request.method == 'DELETE':
            resp = requests.delete(url)
        else:
            logging.warning(f"Method not allowed: {request.method}")
            return "Method Not Allowed", 405

        logging.info(f"Inventory service responded with status {resp.status_code}")
        # Create a Flask response from the requests response
        headers = [(name, value) for (name, value) in resp.headers.items() if name.lower() not in ['content-encoding', 'transfer-encoding', 'connection']]
        response = Response(resp.content, resp.status_code, headers)
        return response

    except requests.exceptions.RequestException as e:
        logging.error(f"Inventory service unavailable: {e}")
        return jsonify({"error": "Inventory service is unavailable", "details": str(e)}), 503

# --- Billing Service Routing ---

@app.route('/api/billing', methods=['POST'])
def post_to_billing_queue():
    """
    Receives a JSON payload and posts it as a message to the RabbitMQ billing_queue.
    """
    data = request.get_json()
    if not data:
        logging.warning("Received invalid billing request: no JSON payload")
        return jsonify({"error": "Invalid JSON payload"}), 400

    logging.info(f"Received billing request: {data}")

    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=BILLING_VM_IP,
                virtual_host=RABBITMQ_VHOST,
                credentials=credentials
            )
        )
        channel = connection.channel()

        # Declare the queue as durable to ensure messages are not lost if RabbitMQ restarts
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

        # Publish the message
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        connection.close()
        
        logging.info("Billing request successfully posted to RabbitMQ")
        return jsonify({"message": "Billing request has been posted successfully"}), 202

    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"Could not connect to RabbitMQ: {e}")
        return jsonify({"error": "Could not connect to the billing service queue", "details": str(e)}), 503
    except Exception as e:
        logging.error(f"An unexpected error occurred while posting to billing queue: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

# --- Health Check ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
