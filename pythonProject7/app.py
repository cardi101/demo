# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from models import db, Request, User, Comment, Executor
from auth import auth as auth_blueprint
from functools import wraps
from sqlalchemy import func
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///requests.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

app.register_blueprint(auth_blueprint)

def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if current_user.role != role:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

@app.route('/')
@login_required
def index():
    if current_user.role == 'user':
        return redirect(url_for('client_view'))
    executors = Executor.query.all()
    return render_template('index.html', executors=executors)

@app.route('/client')
@login_required
@role_required('user')
def client_view():
    user_requests = Request.query.filter_by(client=current_user.name).all()
    return render_template('client.html', requests=user_requests)

@app.route('/add-executor', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_executor():
    if request.method == 'POST':
        name = request.form.get('name')

        if Executor.query.filter_by(name=name).first():
            flash('Executor with this name already exists.', 'error')
            return redirect(url_for('add_executor'))

        new_executor = Executor(name=name)
        db.session.add(new_executor)
        db.session.commit()
        flash('Executor added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_executor.html')

@app.route('/requests', methods=['POST'])
@login_required
@role_required('admin')
def add_request():
    data = request.get_json()
    new_request = Request(
        request_number=data['request_number'],
        equipment=data['equipment'],
        issue_type=data['issue_type'],
        description=data['description'],
        client=data['client'],
        status=data['status']
    )
    db.session.add(new_request)
    db.session.commit()
    flash('Request added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/requests/<int:id>', methods=['PUT'])
@login_required
@role_required('admin')
def edit_request(id):
    data = request.get_json()
    req = Request.query.get(id)
    if req:
        req.status = data.get('status', req.status)
        req.description = data.get('description', req.description)
        req.assigned_to = data.get('assigned_to', req.assigned_to)
        db.session.commit()
        flash('Request updated successfully!', 'success')
        return jsonify({"message": "Request updated successfully!"})
    return jsonify({"message": "Request not found"}), 404

@app.route('/requests/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_request(id):
    req = Request.query.get(id)
    if req:
        db.session.delete(req)
        db.session.commit()
        flash('Request deleted successfully!', 'success')
        return jsonify({"message": "Request deleted successfully!"})
    return jsonify({"message": "Request not found"}), 404

@app.route('/requests/<int:id>', methods=['GET'])
@login_required
def get_request(id):
    req = Request.query.get(id)
    if req:
        comments = [{"text": comment.text, "date_added": comment.date_added} for comment in req.comments]
        return jsonify({
            "request_number": req.request_number,
            "date_added": req.date_added,
            "equipment": req.equipment,
            "issue_type": req.issue_type,
            "description": req.description,
            "client": req.client,
            "status": req.status,
            "assigned_to": req.assigned_to,
            "comments": comments
        })
    return jsonify({"message": "Request not found"}), 404

@app.route('/requests', methods=['GET'])
@login_required
def get_all_requests():
    search_query = request.args.get('search')
    if search_query:
        requests = Request.query.filter(Request.request_number.contains(search_query) |
                                        Request.equipment.contains(search_query) |
                                        Request.issue_type.contains(search_query) |
                                        Request.description.contains(search_query) |
                                        Request.client.contains(search_query)).all()
    else:
        requests = Request.query.all()
    output = []
    for req in requests:
        req_data = {
            "id": req.id,
            "request_number": req.request_number,
            "date_added": req.date_added,
            "equipment": req.equipment,
            "issue_type": req.issue_type,
            "description": req.description,
            "client": req.client,
            "status": req.status,
            "assigned_to": req.assigned_to,
            "comments": [{"text": comment.text, "date_added": comment.date_added} for comment in req.comments]
        }
        output.append(req_data)
    return jsonify(output)

@app.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    total_requests = Request.query.count()
    completed_requests = Request.query.filter_by(status='выполнено').count()
    average_time = db.session.query(func.avg(Request.date_added)).filter(Request.status == 'выполнено').scalar()
    issue_types = db.session.query(Request.issue_type, func.count(Request.issue_type)).group_by(Request.issue_type).all()
    return jsonify({
        "total_requests": total_requests,
        "completed_requests": completed_requests,
        "average_completion_time": average_time,
        "issue_types": issue_types
    })

@app.route('/requests/<int:id>/comments', methods=['POST'])
@login_required
def add_comment(id):
    data = request.get_json()
    req = Request.query.get(id)
    if req:
        new_comment = Comment(text=data['text'], request_id=id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
        return jsonify({"message": "Comment added successfully!"}), 201
    return jsonify({"message": "Request not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
