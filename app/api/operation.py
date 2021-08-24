from flask import jsonify, request
from app import db
from app.api import bp
from app.models import Operation


@bp.route('/operation', methods=['GET'])
def get_operation():
    args = request.args
    row = db.session.query(Operation).first()
    return jsonify(str(row))
