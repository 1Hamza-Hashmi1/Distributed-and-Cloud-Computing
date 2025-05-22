import pika
import grpc
import rover_pb2
import rover_pb2_grpc
import hashlib
import sys
import time


def find_valid_pin(serial_number):
    """Brute-force SHA-256 to find a valid PIN with 6 leading zeros."""
    pin = 0
    while True:
        key = f"{pin}{serial_number}"
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        if hashed_key.startswith("000000"):  # Looking for 6 leading zeros
            return pin
        pin += 1


def process_mine(ch, method, properties, body, deminer_id):
    """Callback function to process incoming mine messages."""
    message = body.decode()
    mine_id, serial_number, x, y = message.split(",")

    print(f"Deminer {deminer_id} received mine {mine_id} at ({x}, {y}) with serial number {serial_number}.")

    start_time = time.time()
    pin = find_valid_pin(serial_number)  # Perform brute-force hashing
    end_time = time.time()

    print(f"Deminer {deminer_id} found PIN {pin} for mine {mine_id} in {end_time - start_time:.2f} seconds.")

    # Publish the PIN to the Defused-Mines queue
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='Defused-Mines')
    channel.basic_publish(exchange='', routing_key='Defused-Mines', body=str(pin))
    connection.close()

    print(f"Deminer {deminer_id} published PIN {pin} to Defused-Mines.")

    # Acknowledge the message so it's removed from the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """Main function for the deminer."""
    if len(sys.argv) != 2:
        print("Usage: python deminer.py <deminer_id>")
        return

    deminer_id = int(sys.argv[1])
    print(f"Deminer {deminer_id} is online and listening for mines...")

    # Set up RabbitMQ subscriber
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='Demine-Queue')

    # Consume messages from the queue
    channel.basic_consume(queue='Demine-Queue',
                          on_message_callback=lambda ch, method, properties, body: process_mine(ch, method, properties,
                                                                                                body, deminer_id))

    print(f"Deminer {deminer_id} is waiting for mine tasks...")
    channel.start_consuming()


if __name__ == '__main__':
    main()
