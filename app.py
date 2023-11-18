import glob
import hashlib
import os
from flask import Flask, jsonify, render_template, request, Response, url_for, redirect, send_file, make_response
from flask_cors import CORS
from google.cloud import storage, datastore
import pip._vendor.requests as requests
from io import BytesIO
from urllib.parse import unquote
import datetime
from flask_jwt_extended import create_access_token, JWTManager
import base64
import json
from urllib.parse import urlparse
from datetime import timedelta


app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET')
jwt = JWTManager(app)

BUCKET_NAME = os.environ.get('BUCKET_NAME')

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION')
with open('google-credentials.json', 'w') as outfile:
    outfile.write(GOOGLE_APPLICATION_CREDENTIALS)


# Client for datastore
storage_client = storage.Client.from_service_account_json(
    'google-credentials.json')
client = datastore.Client.from_service_account_json(
    'google-credentials.json')
uploaded_image_count = 0
user = None


# GET TOKEN FROM DATASTORE
def get_token_from_datastore(username):
    query = client.query(kind='Users')
    query.add_filter('username', '=', username)
    entities = list(query.fetch())

    if entities:
        return entities[0]['token']
    return None


# GET USERNAME FROM COOKIE
def getUsername(cookie):
    if cookie is None:
        return None
    try:
        header, payload, signature = cookie.split('.')

        decoded_payload = base64.urlsafe_b64decode(
            payload + '==').decode('utf-8')
        username = json.loads(decoded_payload)['sub']
        token = get_token_from_datastore(username)
        if token != cookie:
            return None

        return username
    except:
        return None


# ROUTE TO index.html
@app.route('/')
def index():
    cookie = request.cookies.get('access_token')
    username = getUsername(cookie)
    if username is None:
        return redirect(url_for('login'))
    return render_template('index.html', user=username)


# ROUTE TO login.html
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        cookie = request.cookies.get('access_token')
        username = getUsername(cookie)
        if username is not None:
            return redirect(url_for('index'))
        return render_template('login.html')
    elif request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify(message="Username and password are required"), 400

        user_exists, message = check_user_exists(username, password)

        if user_exists:
            access_token = create_access_token(identity=username)
            store_token_in_datastore(username, access_token)
            response = make_response(
                jsonify(message=message, access_token=access_token), 200)
            response.set_cookie('access_token', access_token, httponly=True)
            return response
        else:
            return jsonify(message=message), 400


# STORE TOKEN IN DATASTORE
def store_token_in_datastore(username, token):
    query = client.query(kind='Users')
    query.add_filter('username', '=', username)

    users = list(query.fetch())
    entity = users[0]
    entity.update({
        'username': username,
        'token': token
    })
    client.put(entity)


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
        access_token = create_access_token(identity=username)
        store_token_in_datastore(username, access_token)
        response = make_response(
            jsonify(message=create_message, access_token=access_token), 201)
        response.set_cookie('access_token', access_token, httponly=True)
        return response


# CHECK IF USERNAME EXISTS
def check_username_exists(username):
    query = client.query(kind='Users')
    query.add_filter('username', '=', username)

    users = list(query.fetch())

    if users:
        return True
    else:
        return False


# CREATE USER
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
    cookie = request.cookies.get('access_token')
    username = getUsername(cookie)
    if username is None:
        return jsonify(message="User not logged in"), 400
    store_token_in_datastore(username, '')
    response = make_response(
        jsonify(message="User logged out successfully"), 200)
    response.set_cookie('access_token', '', expires=0, httponly=True)
    return response


# ROUTE TO upload
@app.route('/api/upload', methods=['POST'])
def upload_image():
    cookie = request.cookies.get('access_token')
    username = getUsername(cookie)
    if username is None:
        return jsonify(message="User not logged in"), 400

    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "No image provided"}), 400

    if image:
        print(image.filename)
        try:
            global uploaded_image_count
            filename = username + "_" + \
                str(uploaded_image_count) + "_" + image.filename
            bucket = storage_client.get_bucket(BUCKET_NAME)
            blob = bucket.blob(filename)
            blob.upload_from_string(
                image.read(), content_type=image.content_type)

            imageData = {
                "image_name": filename,
                "url": '/images/' + filename,
                "size": blob.size,
                "content_type": blob.content_type,
                "upload_date": blob.time_created.strftime("%Y-%m-%d")
            }
            uploaded_image_count += 1
            return jsonify({"message": "Image uploaded successfully", "data": imageData}), 200
        except (Exception) as error:
            print("Failed to upload image to GCS")
            return jsonify({"error": "Failed to upload image to GCS", "msg": error.args}), 500


def generate_signed_url(object_name):
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(object_name)
    signed_url = blob.generate_signed_url(
        expiration=timedelta(minutes=30))
    return signed_url


# GENERATE SIGNED URL
@app.route('/images/<image_id>')
def serve_image(image_id):
    signed_url = generate_signed_url(image_id)
    return redirect(signed_url)


# ROUTE TO get all images
@app.route('/api/images')
def get_all_images():
    cookie = request.cookies.get('access_token')
    username = getUsername(cookie)
    global uploaded_image_count
    query = client.query(kind='Image')
    query.add_filter('user_id', '=', username)

    results = list(query.fetch())

    if not results:
        uploaded_image_count = 0
        return jsonify(results), 200

    uploaded_image_count = len(results)

    for result in results:
        result['id'] = result.key.id
        result['url'] = '/images/' + result['image_name']

    # for result in results:
    #     result['id'] = result.key.id
    #     object_name = result['image_name']
    #     bucket = storage_client.get_bucket(BUCKET_NAME)
    #     blob = bucket.blob(object_name)
    #     result['url'] = '/images/' + result['image_name']
    #     expiration = datetime.timedelta(minutes=1)
    #     signed_url = blob.generate_signed_url(expiration=expiration)
    #     print(signed_url)

    return jsonify(results), 200


# ROUTE TO DELETE image
@app.route('/api/delete-image', methods=['DELETE'])
def delete_image():
    try:
        data = request.json
        image_url = data.get('url')
        print(image_url)
        if not image_url:
            return jsonify(error='Image name is required'), 400

        image_name = unquote(image_url.split("/")[-1])

        bucket = storage_client.get_bucket(BUCKET_NAME)
        blob = bucket.blob(image_name)
        blob.delete()

        # Delete the metadata from the Datastore
        query = client.query(kind='Image')
        query.add_filter('image_name', '=', image_name)
        entities = list(query.fetch())

        if not entities:
            return jsonify(error='Image metadata not found'), 404

        entity_key = entities[0].key
        client.delete(entity_key)

        return jsonify(message='Image and metadata deleted successfully'), 200
    except Exception as e:
        print(e)  # For development/debugging purposes
        return jsonify(error='An error occurred while trying to delete the image and metadata'), 500


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
