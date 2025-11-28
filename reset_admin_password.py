"""重置 admin 密码为原始密码"""
from flask_backend.app.database.mongodb import get_db
from flask_backend.app.database.init_db import hash_password, generate_salt

db = get_db()
salt = generate_salt()
password_hash = hash_password('izBjsfvGqwJ0Qnxy', salt)
result = db.users.update_one(
    {'username': 'admin'}, 
    {'$set': {'password': password_hash}}
)
print(f'Password reset successful: {result.modified_count} document(s) modified')
