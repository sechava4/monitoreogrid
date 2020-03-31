from app import app
from flask import Flask, url_for

app.run(debug=True, port=8086)
# app.run(host='0.0.0.0', debug=True, port=8080)
# app.add_url_rule('/favicon.ico',redirect_to=url_for('static', filename='monitor.ico'))

