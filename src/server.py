#!/usr/bin/env python
# encoding: utf-8
import datetime
import json
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
import os
from OpenSSL import crypto
from hashlib import sha256

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': os.getenv('MONGODB_DB'),
    'host': os.getenv('MONGODB_HOST'),
    'port': int(os.getenv('MONGODB_PORT'))
}
db = MongoEngine()
db.init_app(app)


class FeedPost(db.Document):
    meta = {'collection': os.getenv('DB_COLLECTION_NAME_FEED_POST')}
    userId = db.StringField()
    contentReference = db.StringField()
    timestamp = db.DateTimeField()


@app.route("/feed", methods=['GET'])
def index():
    user_cert = request.headers.get("X-Client-Cert")
    if user_cert:
        cert_object = crypto.load_certificate(crypto.FILETYPE_PEM, user_cert)
        pub_key_object = cert_object.get_pubkey()
        pub_key_string = crypto.dump_publickey(crypto.FILETYPE_PEM, pub_key_object)
        user_id = sha256(pub_key_string).hexdigest()

        entries = FeedPost.objects(userId=user_id).order_by('-timestamp')
        response_entries = []
        for entry in entries:
            response_entries.append({
                "userId": entry.userId,
                "contentReference": entry.contentReference,
                "createdOn": entry.timestamp.isoformat()
            })
        return jsonify(response_entries), 200
    else:
        return {}, 401


@app.route("/redact/relay", methods=['POST'])
def redact_relay():
    user_cert = request.headers.get("X-Client-Cert")
    if user_cert:
        crtObj = crypto.load_certificate(crypto.FILETYPE_PEM, user_cert)
        pubKeyObject = crtObj.get_pubkey()
        pubKeyString = crypto.dump_publickey(crypto.FILETYPE_PEM, pubKeyObject)
        userId = sha256(pubKeyString).hexdigest()

        FeedPost.objects.insert(FeedPost(
            userId=userId,
            contentReference=request.json['path'],
            timestamp=datetime.datetime.now())
        )
        return {}, 200
    else:
        return {}, 401


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='8080')

app.run(host='0.0.0.0', port='8080')
