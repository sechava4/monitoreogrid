from dictalchemy.utils import make_class_dictable
from flask import jsonify, request

from app.api import bp
from app.models import Operation


@bp.route('/returndata')
def returndata():
    placa = request.args.get('placa')
    make_class_dictable(Operation)
    query = Operation.query.filter(Operation.vehicle_id == placa).order_by(Operation.id.desc()).first()
    return jsonify(query.asdict())
