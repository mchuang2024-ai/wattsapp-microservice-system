import pika
import time


def create_connection(hostname, port):
    retries = 0
    max_retries = 12

    while retries < max_retries:
        try:
            print(f"Connecting to AMQP broker {hostname}:{port}...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=hostname,
                    port=port,
                    heartbeat=3600,
                    blocked_connection_timeout=3600,
                )
            )
            print("Connection established!")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            retries += 1
            print(f"Connection failed: {e}")
            if retries < max_retries:
                print(f"Retrying in 5 seconds... ({retries}/{max_retries})")
                time.sleep(5)

    raise Exception(
        f"Failed to connect to AMQP broker after {max_retries} retries."
    )


def check_setup(hostname, port, exchangename, exchangetype):
    """
    Creates a connection and declares the named exchange.
    Returns (connection, channel).
    """
    connection = create_connection(hostname, port)
    channel = connection.channel()
    channel.exchange_declare(
        exchange=exchangename,
        exchange_type=exchangetype,
        durable=True,
    )
    return connection, channel


def start_consuming(hostname, port, exchangename, exchangetype, queue, callback):
    """
    Declares the exchange and queue, binds the queue to the exchange
    (no routing key — receives all messages), then starts consuming.
    Use check_setup() directly when you need per-routing-key bindings.
    """
    connection, channel = check_setup(hostname, port, exchangename, exchangetype)

    channel.queue_declare(queue=queue, durable=True)
    channel.queue_bind(exchange=exchangename, queue=queue)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)

    print(f"Waiting for messages on queue '{queue}'. To exit press CTRL+C")
    channel.start_consuming()
