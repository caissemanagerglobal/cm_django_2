from flask import Flask, request, jsonify
from printer import process_print_job
import pika
import json
from escpos.printer import Network
from PIL import Image
import io
import json

app = Flask(__name__)

@app.route('/print', methods=['POST'])
def print_receipt():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    def callback(body):
        data = body
        printer_ip = data.get('printer_ip')
        image_content = data.get('image_content')
        cashdraw = data.get('cashdraw')

        # Convert string back to bytes
        image_bytes = image_content.encode('latin1')

        image = Image.open(io.BytesIO(image_bytes))

        printer = Network(printer_ip)
        # printer.text("Printing receipt...\n")
        printer.image(image)
        printer.cut()
        if cashdraw:
            open_drawer_command = b'\x1b\x70\x00\x19\xfa'
            printer._raw(open_drawer_command)
        printer.close()
    
    callback(data)

    # job_id = process_print_job(data)
    return jsonify({"job_id": "2"}), 202


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
 