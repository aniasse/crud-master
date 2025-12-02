import os
import pika
import json
import psycopg2
from psycopg2 import sql
import time

# --- Database Configuration ---
db_user = os.environ.get('BILLING_DB_USER', 'billing_user')
db_password = os.environ.get('BILLING_DB_PASSWORD', 'billing_password')
db_name = os.environ.get('BILLING_DB_NAME', 'billing_db')
db_host = 'localhost' # Running on the same VM

# --- RabbitMQ Configuration ---
rabbitmq_user = os.environ.get('RABBITMQ_USER', 'rabbitmq_user')
rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD', 'rabbitmq_password')
rabbitmq_vhost = os.environ.get('RABBITMQ_VHOST', 'billing_vhost')
rabbitmq_queue = os.environ.get('RABBITMQ_QUEUE', 'billing_queue')
rabbitmq_host = 'localhost' # Running on the same VM

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    while True:
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host
            )
            print("--- Database connection established. ---")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def create_orders_table():
    """Creates the 'orders' table if it doesn't exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                number_of_items INTEGER NOT NULL,
                total_amount NUMERIC(10, 2) NOT NULL,
                received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("--- 'orders' table created or already exists. ---")
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def process_billing_message(ch, method, properties, body):
    """Callback function to process a message from RabbitMQ."""
    print(f"--- Received message: {body} ---")
    try:
        message = json.loads(body)
        
        user_id = message.get('user_id')
        number_of_items = message.get('number_of_items')
        total_amount = message.get('total_amount')

        if not all([user_id, number_of_items, total_amount]):
            print("Message is missing required fields. Rejecting.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        conn = get_db_connection()
        cur = conn.cursor()
        
        insert_query = sql.SQL("""
            INSERT INTO orders (user_id, number_of_items, total_amount)
            VALUES (%s, %s, %s);
        """)
        
        cur.execute(insert_query, (str(user_id), int(number_of_items), float(total_amount)))
        conn.commit()
        
        print("--- Order data inserted into database. ---")
        
        cur.close()
        conn.close()
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print("--- Message acknowledged. ---")

    except json.JSONDecodeError:
        print("Failed to decode JSON. Rejecting message.")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except (psycopg2.Error, ValueError) as e:
        print(f"Database or data error: {e}. Re-queueing message.")
        # Re-queue the message to be processed again later
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}. Rejecting message.")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """Main function to set up and start the consumer."""
    # Ensure the database and table exist before consuming
    create_orders_table()

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=rabbitmq_host,
                    virtual_host=rabbitmq_vhost,
                    credentials=credentials
                )
            )
            channel = connection.channel()
            
            # Declare the queue, durable=True makes it survive broker restart
            channel.queue_declare(queue=rabbitmq_queue, durable=True)
            
            # Set prefetch_count=1 to ensure that the worker only receives one message at a time
            channel.basic_qos(prefetch_count=1)
            
            channel.basic_consume(
                queue=rabbitmq_queue,
                on_message_callback=process_billing_message
            )
            
            print(f"--- Waiting for messages in queue '{rabbitmq_queue}'. To exit press CTRL+C ---")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred in main loop: {e}. Restarting...")
            time.sleep(5)


if __name__ == '__main__':
    main()
