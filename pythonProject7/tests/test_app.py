# tests/test_app.py
import unittest
from app import app, db
from models import User, Request, Executor
from flask import jsonify
from werkzeug.security import generate_password_hash

class BasicTests(unittest.TestCase):

    # Setup and Teardown
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_requests.db'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            self.create_test_data()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def create_test_data(self):
        user1 = User(email='admin@test.com', password=generate_password_hash('password', method='sha256'), name='Admin User', role='admin')
        user2 = User(email='user@test.com', password=generate_password_hash('password', method='sha256'), name='Regular User', role='user')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

    # Helper methods
    def login(self, email, password):
        return self.app.post('/login', data=dict(email=email, password=password), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def add_request(self, request_data):
        return self.app.post('/requests', json=request_data, follow_redirects=True)

    def edit_request(self, request_id, update_data):
        return self.app.put(f'/requests/{request_id}', json=update_data, follow_redirects=True)

    def delete_request(self, request_id):
        return self.app.delete(f'/requests/{request_id}', follow_redirects=True)

    def add_executor(self, executor_data):
        return self.app.post('/add-executor', data=executor_data, follow_redirects=True)

    # Tests
    def test_login_logout(self):
        response = self.login('admin@test.com', 'password')
        self.assertIn(b'Logout', response.data)
        response = self.logout()
        self.assertIn(b'Login', response.data)

    def test_add_request(self):
        self.login('admin@test.com', 'password')
        request_data = {
            'request_number': 'REQ001',
            'equipment': 'Laptop',
            'issue_type': 'Screen Issue',
            'description': 'Screen is flickering',
            'client': 'Client A',
            'status': 'в ожидании'
        }
        response = self.add_request(request_data)
        self.assertIn(b'Request added successfully!', response.data)

    def test_edit_request(self):
        self.login('admin@test.com', 'password')
        request_data = {
            'request_number': 'REQ002',
            'equipment': 'Desktop',
            'issue_type': 'Power Issue',
            'description': 'Computer will not power on',
            'client': 'Client B',
            'status': 'в ожидании'
        }
        self.add_request(request_data)
        update_data = {
            'status': 'в работе',
            'description': 'Power supply replaced',
            'assigned_to': 'Executor 1'
        }
        response = self.edit_request(1, update_data)
        self.assertIn(b'Request updated successfully!', response.data)

    def test_delete_request(self):
        self.login('admin@test.com', 'password')
        request_data = {
            'request_number': 'REQ003',
            'equipment': 'Printer',
            'issue_type': 'Paper Jam',
            'description': 'Paper gets jammed frequently',
            'client': 'Client C',
            'status': 'в ожидании'
        }
        self.add_request(request_data)
        response = self.delete_request(1)
        self.assertIn(b'Request deleted successfully!', response.data)

    def test_add_executor(self):
        self.login('admin@test.com', 'password')
        executor_data = {
            'name': 'Executor 1'
        }
        response = self.add_executor(executor_data)
        self.assertIn(b'Executor added successfully!', response.data)

    def test_assign_executor_to_request(self):
        self.login('admin@test.com', 'password')
        request_data = {
            'request_number': 'REQ004',
            'equipment': 'Monitor',
            'issue_type': 'No Display',
            'description': 'Monitor does not display anything',
            'client': 'Client D',
            'status': 'в ожидании'
        }
        self.add_request(request_data)
        executor_data = {
            'name': 'Executor 2'
        }
        self.add_executor(executor_data)
        update_data = {
            'assigned_to': 'Executor 2'
        }
        response = self.edit_request(1, update_data)
        self.assertIn(b'Request updated successfully!', response.data)

if __name__ == "__main__":
    unittest.main()
