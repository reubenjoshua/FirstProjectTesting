from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import pytz
from sqlalchemy import or_

app = Flask(__name__)
CORS(app)

PH_TZ = pytz.timezone("Asia/Manila")

app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://dev_josh:reubenjoshua10@localhost/TaskDB?driver=ODBC+Driver+17+for+SQL+Server"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(PH_TZ))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(PH_TZ))
    deleted_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'deleted_at': self.deleted_at.strftime('%Y-%m-%d %H:%M:%S') if self.deleted_at else None,
        }

with app.app_context():
    db.create_all()

@app.route('/tasks', methods=['GET'])
def get_tasks():
    search_query = request.args.get('search', '', type=str)
    include_deleted = request.args.get('include_deleted', 'false', type=str).lower() == 'true'

    query = Task.query

    if search_query:
        query = query.filter(or_(
            Task.title.ilike(f"%{search_query}%"),
            Task.created_at.cast(db.String).ilike(f"%{search_query}%"),
            Task.updated_at.cast(db.String).ilike(f"%{search_query}%"),
            Task.deleted_at.cast(db.String).ilike(f"%{search_query}%")
        ))

    if not include_deleted:
        query = query.filter(Task.deleted_at == None)

    tasks = query.all()

    return jsonify([task.to_dict() for task in tasks])

@app.route('/tasks', methods=['POST'])
def add_tasks():
    data = request.json
    new_task = Task(title=data['title'])
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task added successfully', 'task': new_task.to_dict()}), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.json
    if not data or 'title' not in data:
        return jsonify({"error": "Missing 'title' field"}), 400

    task.title = data['title']
    task.updated_at = datetime.now(PH_TZ)
    db.session.commit()

    return jsonify(task.to_dict())

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task or task.deleted_at:
        return jsonify({'error': 'Task not found'}), 404

    task.deleted_at = datetime.now(PH_TZ)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)

