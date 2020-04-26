from app import app, db
from app.models import User, Vehicle, Station, Operation, Task

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Vehicle': Vehicle, 'Station': Station,
            'Operation': Operation, 'Task': Task}

app.run(debug=True, port=8080)
# app.run(host='0.0.0.0', debug=True, port=8080)

