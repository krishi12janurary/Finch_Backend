from functools import wraps
from flask import abort,g # g is an special function in flask which helps to return or send some important or anything to get into main function.
from flask_jwt_extended import get_jwt_identity,jwt_required
from models import User
def check_current_user(insert_demat_record):#while insert_demat_record is just an varaible which intakes the function and return the wrapper.
    @wraps(insert_demat_record)#okay so we wrote wraps so that however or whichever the routes function name passed they hold their own identity for example function name buy-sell is being introduce than the wrapper will function and work as per what logic has been given and check it but before wraps the wrapper who was rebuilding the function actual and real identity like name after that wraps it will not happen.
    def wrapper(*args,**kwargs):
        current_user = get_jwt_identity()
        user_exists = User.query.filter_by(email=current_user).first()
        if not user_exists:
            return "User not exists"
        return insert_demat_record(user_exists, *args,**kwargs)#now writing args and kwargs becuase without these the original function will not execute so basically keeping them only because for flexibility and if with returning the function if we want to pass any arguments, keyword-arguments like return user_login(user_id,result(key,argu)) if there while if not than even than we pass the args and kwargs is mandatory.
    
    return wrapper

#now what i am understanding is we have create an function under one
#  function now let's say we have cereated login route with function name 
# user_login now when we are building wrapper we will write this user_login wala 
# function name into first function and under that we will write our condition 
# which we want to wrap and run when someone call now when user is nnot 
# found we will return user not found error and if we found than the main function 
# user_login will run and continue with the logic now while when we write return
#  wrapper at the end there we means whatever inside the wrapper is being mentioned 
# and conditioned that will be run but i didn't understand 1 thing that why we are
#  returining user_login with *args and **kwargs?  mean not though we are passing 
# the arguments or nothing like that?
        
