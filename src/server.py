#!/usr/bin/env python
# encoding: utf-8
import datetime
import json
import uuid
import jwt

from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
import os
from OpenSSL import crypto
from hashlib import sha256
from flask_socketio import SocketIO
import urllib.parse

from jwt import ExpiredSignatureError

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': os.getenv('MONGODB_DB'),
    'host': os.getenv('MONGODB_HOST'),
    'port': int(os.getenv('MONGODB_PORT')),
}
app.config['jwt_secret_key'] = os.getenv('JWT_SECRET_KEY')
db = MongoEngine()
db.init_app(app)
socketio = SocketIO(app)


class FeedPost(db.Document):
    meta = {'collection': os.getenv('DB_COLLECTION_NAME_FEED_POST')}
    userId = db.StringField()
    contentReference = db.StringField()
    timestamp = db.DateTimeField()


@app.route("/feed", methods=['GET'])
def index():
    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return {}, 401

    user_id = None
    try:
        jwt_payload = jwt.decode(
            auth_token.replace('Bearer ', ''),
            key=app.config.get('jwt_secret_key'),
            algorithms=['HS256']
        )
        user_id = jwt_payload.get('user_id')
    except ExpiredSignatureError as error:
        print(f'Unable to decode the token, error: {error}')

    if not user_id:
        return {}, 401

    skip = request.args.get('skip', default=0, type=int)
    limit = request.args.get('limit', default=20, type=int)
    if int(limit) > 20:
        limit = 20

    entries = FeedPost.objects(userId=user_id).limit(limit).skip(skip).order_by('-timestamp')
    response_entries = []
    for entry in entries:
        response_entries.append({
            "userId": entry.userId,
            "contentReference": entry.contentReference,
            "createdOn": entry.timestamp.isoformat()
        })
    return jsonify(response_entries), 200


@app.route("/redact/relay", methods=['POST'])
def redact_relay():
    user_cert = request.headers.get("X-Client-Cert")
    auth_token = request.headers.get("Authorization")

    if not user_cert:
        return {}, 401

    formatted_cert = user_cert.replace('\\n', '\n').replace('\\t', '\t')
    formatted_cert = urllib.parse.unquote(formatted_cert)
    crtObj = crypto.load_certificate(crypto.FILETYPE_PEM, formatted_cert)
    pubKeyObject = crtObj.get_pubkey()
    pubKeyString = crypto.dump_publickey(crypto.FILETYPE_PEM, pubKeyObject)
    userId = sha256(pubKeyString).hexdigest()

    FeedPost.objects.insert(FeedPost(
        userId=userId,
        contentReference=request.json['path'],
        timestamp=datetime.datetime.now())
    )

    # TODO
    # socketio.send({"path": request.json['path']}).to(auth_token.get("user_id"))
    return {}, 200


@app.route("/redact/session_create", methods=['GET'])
def redact_session_create():
    user_cert = request.headers.get("X-Client-Cert")
    if not user_cert:
        return {}, 401

    formatted_cert = user_cert.replace('\\n', '\n').replace('\\t', '\t')
    formatted_cert = urllib.parse.unquote(formatted_cert)

    crtObj = crypto.load_certificate(crypto.FILETYPE_PEM, formatted_cert)
    pubKeyObject = crtObj.get_pubkey()
    pubKeyString = crypto.dump_publickey(crypto.FILETYPE_PEM, pubKeyObject)
    user_id = sha256(pubKeyString).hexdigest()

    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=0),
            'iat': datetime.datetime.utcnow(),
            'user_id': user_id,
            'session_id': str(uuid.uuid4())
        }
        auth_token = jwt.encode(
            payload,
            app.config.get('jwt_secret_key'),
            algorithm='HS256'
        )

        return {"auth_token": auth_token}, 200
    except Exception as e:
        # TODO: log error
        return {}, 500


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port='5000')
