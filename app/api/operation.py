from flask import jsonify, request
from app import db
from app.api import bp
from app.models import Operation
import pandas as pd
import json

@bp.route('/returndata')
def returndata():
    placa= request.args.get('placa')
    query = 'SELECT * FROM operation WHERE placa = "' + str(placa) + '" ORDER BY id DESC LIMIT 1'
    #query = Operation.query.filter_by(placa=placa).order_by(Operation.id.desc()).first()
    print(query)
    df_vehicles = pd.read_sql_query(query, db.engine)
    result = df_vehicles.to_json(orient="split")
    parsed = json.loads(result)
    return jsonify(parsed)

