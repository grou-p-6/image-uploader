import os
from flask import Flask, jsonify, render_template, request, Response, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'static/uploaded_images'
uploaded_image_count = 0

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# update the uplodaed_image_count by checking the number of files present in the upload_folder
uploaded_image_count = len(os.listdir(UPLOAD_FOLDER))


# route to index.html

@app.route('/')
def index():
    return render_template('index.html')


# route to upload.html

@app.route('/api/upload', methods=['POST'])
def upload_image():
    print("Reached upload_image")
    global uploaded_image_count

    # Check if the post request has the file part.
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No selected image"}), 400

    if image:
        filename = os.path.join(UPLOAD_FOLDER, str(
            uploaded_image_count) + "_" + image.filename)
        image.save(filename)

        file_url = url_for('static', filename=os.path.join('uploaded_images', str(
            uploaded_image_count) + "_" + image.filename), _external=True)
        print(file_url)
        uploaded_image_count += 1
        return jsonify({"message": "Image uploaded successfully", "len": uploaded_image_count, "url": file_url}), 200


# route to get image by id

@app.route('/api/images/<path:image_name>')
def get_image(image_name):
    # Ensure filename is secure
    image_name = os.path.basename(image_name)

    # Check if file exists
    if not os.path.isfile(os.path.join(UPLOAD_FOLDER, image_name)):
        return jsonify({"error": "File not found."}), 404

    # Constructing the URL for the requested file.
    file_url = url_for('static', filename=os.path.join(
        'uploaded_images', image_name), _external=True)

    return jsonify({"file_url": file_url}), 200


# route to get all images

@app.route('/api/images')
def get_all_images():
    image_files = [f for f in os.listdir(
        UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]

    image_urls = [url_for('static', filename=os.path.join(
        'uploaded_images', image_file), _external=True) for image_file in image_files]

    return jsonify({"image_urls": image_urls})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)