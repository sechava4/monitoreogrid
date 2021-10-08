from dictalchemy.utils import make_class_dictable
from flask import jsonify, request

from managev_app.api import bp
from managev_app.models import Operation


@bp.route("/returndata")
def returndata():
    placa = request.args.get("placa")
    make_class_dictable(Operation)
    query = (
        Operation.query.filter(Operation.vehicle_id == placa)
        .order_by(Operation.id.desc())
        .limit(5)
    )
    return jsonify(query.asdict())
