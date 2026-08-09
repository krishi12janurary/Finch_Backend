from functools import wraps
from flask import abort,g # g is an special function in flask which helps to return or send some important or anything to get into main function.
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
        
        # g.current_user = user_verify.id  #now here g stores the value in key-value pair so in we write here to ensure that if the current user is admin than only the current_user -id pass to function. while this g now has stores and works as locker which keep the key-value pairs inside it and with return we don't have to explicity write with return so it;s like jwt-token but here with g we can pass multiple key-value pair like g.current_user = user.id g.current_user_email = email like these and in the function we can retieve it.
        
        return f(*args,**kwargs)
    return decorated_function



