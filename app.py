import glob
import hashlib
import os
from flask import Flask, jsonify, render_template, request, Response, url_for, redirect, send_file
from flask_cors import CORS
from google.cloud import storage, datastore
import pip._vendor.requests as requests
from io import BytesIO
from urllib.parse import unquote


app = Flask(__name__)
CORS(app)

BUCKET_NAME = 'images_g6p2'


# Client for datastore
client = datastore.Client()

uploaded_image_count = 0

user = None


# ROUTE TO index.html
@app.route('/')
def index():
    global user
    if user is None:
        return redirect(url_for('login'))
    return render_template('index.html', user=user)


# ROUTE TO login.html
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify(message="Username and password are required"), 400

        user_exists, message = check_user_exists(username, password)

        if user_exists:
            global user
            user = username
            return jsonify(message=message), 200
        else:
            return jsonify(message=message), 400


# check if user exists
def check_user_exists(username, password):
    query = client.query(kind='Users')
    query.add_filter('username', '=', username)

    users = list(query.fetch())

    if users:
        stored_password_hash = users[0]['password']
        if stored_password_hash == hashlib.sha256(password.encode()).hexdigest():
            return True, "User authenticated successfully"
        else:
            return False, "Incorrect password"
    else:
        return False, "User does not exist"


# route for signup
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(message="Username and password are required"), 400

    user_exists = check_username_exists(username)

    if user_exists:
        return jsonify(message="Username already exists"), 400
    else:
        create_message = create_user(username, password)
        global user
        user = username
        return jsonify(message=create_message), 201


def check_username_exists(username):
    query = client.query(kind='Users')
    query.add_filter('username', '=', username)

    users = list(query.fetch())

    if users:
        return True
    else:
        return False


def create_user(username, password):
    print("|Creating user|")
    key = client.key('Users')
    new_user = datastore.Entity(key=key)
    new_user.update({
        'username': username,
        # Storing password as a hash for security
        'password': hashlib.sha256(password.encode()).hexdigest()
    })
    client.put(new_user)
    return "User created successfully"


# ROUTE TO logout
@app.route('/api/logout', methods=['POST'])
def logout():
    global user
    user = None
    return jsonify(message="User logged out successfully"), 200


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
            global uploaded_image_count, user
            filename = user + "_" + \
                str(uploaded_image_count) + "_" + image.filename
            client = storage.Client()
            bucket = client.get_bucket(BUCKET_NAME)
            blob = bucket.blob(filename)
            blob.upload_from_string(image.read())

            blob.make_public()

            imageData = {
                "image_name": filename,
                "url": blob.public_url,
                "size": blob.size,
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
    global uploaded_image_count, user
    query = client.query(kind='Image')
    query.add_filter('user_id', '=', user)

    results = list(query.fetch())

    if not results:
        uploaded_image_count = 0
        return jsonify(results), 404

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

    if not checkURLOwner(image_url):
        return jsonify(message="Image does not belong to the user"), 400

    response = requests.get(image_url)
    image = BytesIO(response.content)

    imageName = unquote(image_url.split("/")[-1])

    return send_file(image, as_attachment=True, download_name=imageName)


# check if url belongs to the user
def checkURLOwner(image_url):
    global user
    query = client.query(kind='Image')

    query.add_filter('url', '=', image_url)
    query.add_filter('user_id', '=', user)

    results = list(query.fetch())

    if not results:
        return False
    else:
        return True


if __name__ == "__main__":
    # extra_files = glob.glob('templates/*.html', recursive=True) + \
    #     glob.glob('static/**/*.css', recursive=True)
    # app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)),
    #         extra_files=extra_files, debug=True)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
