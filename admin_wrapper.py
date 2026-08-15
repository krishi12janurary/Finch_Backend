from functools import wraps
from flask import abort,g 
from flask_jwt_extended import get_jwt_identity,jwt_required
from models import User
def admin_required(f):
    @wraps(f)
    
    def decorated_function(*args,**kwargs):
        user_email = get_jwt_identity()
        user_verify = User.query.filter_by(email=user_email).first()
        if not user_verify:
            return abort(401)
        
        elif user_verify.role != "admin":
            return abort(403)
        
        g.current_user = user_verify.email
        
        
        
        return f(*args,**kwargs)
    return decorated_function



