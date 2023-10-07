from flask import Flask, jsonify, render_template, request, Response, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

uploaded_image_data = []

# route to index.html


@app.route('/')
def index():
    return render_template('index.html')

# route to upload.html


@app.route('/api/upload', methods=['POST'])
def upload_image():
    print("Reached upload_image")
    global uploaded_image_data

    # Check if the post request has the file part.
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No selected image"}), 400

    if image:
        # Save image data to variable.
        image_content = image.read()
        uploaded_image_data.append(image_content)
        # Return the url of the uploaded image.
        url = url_for('get_image', image_id=len(
            uploaded_image_data) - 1, _external=True)
        return jsonify({"message": "Image uploaded successfully", "len": len(uploaded_image_data), "url": url}), 200

# route to get image by id


@app.route('/api/images/<int:image_id>')
def get_image(image_id):
    if 0 <= image_id < len(uploaded_image_data):
        return Response(uploaded_image_data[image_id], content_type='image/jpeg')
    else:
        return jsonify({"message": "Image not found"}), 404

# route to get total image count


@app.route('/api/image_count')
def get_image_count():
    return jsonify({"total_images": len(uploaded_image_data)})

# route to get all images


@app.route('/api/images')
def get_all_images():
    image_urls = [url_for('get_image', image_id=i, _external=True)
                  for i in range(len(uploaded_image_data))]
    return jsonify(image_urls)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)