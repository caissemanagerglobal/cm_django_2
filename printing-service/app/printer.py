import pika
import json
from escpos.printer import Network
from PIL import Image
import io

def process_print_job(data):
    credentials = pika.PlainCredentials('cm_user', 'CmPass')
    connection_params = pika.ConnectionParameters(host='rabbitmq', credentials=credentials)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue='print_jobs')

    channel.basic_publish(
        exchange='',
        routing_key='print_jobs',
        body=json.dumps(data)
    )

    connection.close()
    return "queued"

def consume_print_jobs():
    credentials = pika.PlainCredentials('cm_user', 'CmPass')
    connection_params = pika.ConnectionParameters(host='rabbitmq', credentials=credentials)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue='print_jobs')

    def callback(ch, method, properties, body):
        data = json.loads(body)
        printer_ip = data.get('printer_ip')
        image_content = data.get('image_content')

        # Convert string back to bytes
        image_bytes = image_content.encode('latin1')

        # Load the image
        image = Image.open(io.BytesIO(image_bytes))

        printer = Network(printer_ip)
        printer.text("Printing receipt...\n")
        printer.image(image)
        printer.cut()

    channel.basic_consume(queue='print_jobs', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    consume_print_jobs()
