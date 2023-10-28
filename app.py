import glob
import hashlib
import os
from flask import Flask, jsonify, render_template, request, Response, url_for, redirect, send_file, make_response
from flask_cors import CORS
from google.cloud import storage, datastore
import pip._vendor.requests as requests
from io import BytesIO
from urllib.parse import unquote


app = Flask(__name__)
CORS(app)

BUCKET_NAME = os.environ.get('BUCKET_NAME')


# Client for datastore
storage_client = storage.Client()

client = datastore.Client()

uploaded_image_count = 0


# ROUTE TO index.html
@app.route('/')
def index():
    return render_template('index.html')


# ROUTE TO upload
@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No image provided"}), 400

    if image:
        print(image.filename)
        try:
            global uploaded_image_count
            filename = "userId_" + \
                str(uploaded_image_count) + "_" + image.filename
            bucket = storage_client.get_bucket(BUCKET_NAME)
            blob = bucket.blob(filename)
            blob.upload_from_string(
                image.read(), content_type=image.content_type)

            blob.make_public()

            imageData = {
                "image_name": filename,
                "url": blob.public_url,
                "size": blob.size,
                "content_type": blob.content_type,
                "upload_date": blob.time_created.strftime("%Y-%m-%d")
            }
            uploaded_image_count += 1
            return jsonify({"message": "Image uploaded successfully", "data": imageData}), 200
        except (Exception) as error:
            print("Failed to upload image to GCS")
            return jsonify({"error": "Failed to upload image to GCS", "msg": error.args}), 500


# ROUTE TO get all images
@app.route('/api/images')
def get_all_images():
    global uploaded_image_count
    query = client.query(kind='Image')

    results = list(query.fetch())

    if not results:
        uploaded_image_count = 0
        return jsonify(results), 200

    uploaded_image_count = len(results)

    for result in results:
        result['id'] = result.key.id

    return jsonify(results), 200


# ROUTE TO download image
@app.route('/api/download-image', methods=['POST'])
def download_image():
    data = request.json
    image_url = data.get('url')

    if not image_url:
        return jsonify(message="Image url is required"), 400

    response = requests.get(image_url)
    image = BytesIO(response.content)

    imageName = unquote(image_url.split("/")[-1])

    return send_file(image, as_attachment=True, download_name=imageName)


if __name__ == "__main__":
    # extra_files = glob.glob('templates/*.html', recursive=True) + \
    #     glob.glob('static/**/*.css', recursive=True) + \
    #     glob.glob('static/**/*.js', recursive=True)
    # app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)),
    #         extra_files=extra_files, debug=True)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
