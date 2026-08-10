
from flask import Flask, jsonify, request,g,session
from extensions import db
from models import User, Account, Transaction, KYC_Model,DematHoldings,DematAccount,UserAdditionalInfo
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, set_access_cookies
import yfinance as yf
from flask_cors import CORS
import razorpay
import uuid #uuid refers to Universally unique identifier.
from datetime import date, timedelta,datetime
from user_wrapper import check_current_user
from sqlalchemy import func
from admin_wrapper import admin_required
import os
from ocr_check import verifying_ocr
from flask_mail import Mail, Message
import secrets
import random
from flask_socketio import SocketIO
from market_data_as_per_timeframe import fetching_50_companies
from listed_company_lists import companys_lists
from portfolio_grouped_comapny import fetching_current_price
from sector_wise_companies import identify_the_sector
from bank_connection import app_login,submitting_kyc_form,collecting_user_status,bank_add_balance,updation_bal_route,demat_acc_approval
import requests
import os
from dotenv import load_dotenv
from geopy.distance import geodesic
load_dotenv()






app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[#We are allowing our React frontend to call backend APIs. Backend must specify which frontend origins are trusted. CORS is the rule/configuration that tells the browser whether to allow that frontend to read the backend response.
    "http://localhost:5173", #now localhost mmeans it's an network which works only at the same device so if we are running our frontend in laptop than only through locahost we can access it but if we want to access that frontend in our phone than we have to connect with the IP address of our wifi network through which both backend and frontend are connected and through that IP address we can access the frontend in our phone and same applies to backend if we want to access backend in phone than also we have to connect with the same wifi network and through that IP address we can access backend in phone.
    "http://192.168.1.4:5173",# this is an IP addresss of my wifi network through which backend and frontend both are connected. that means if my phone wants to talk to my laptop network of backend than they can talk through wifi-network like if phone wants to talk with frontend they first have to connect with wifi network than at port 5173 they can talk to frontend and same applies to backend at port 5000 it;s like if you want something to perform from backend tell it via network wifi .
    "http://127.0.0.1:5173"
    #basically aapde same network etle use kariye che kemke agar user koi bhi reuqest ke message ke activity mokalse ee same network ma male so at the time jyare developer ne check karvu hoy ke aa user verify che ke nai tho backend ma joi ne updte kari sake so the main thing was that both requests and repsonse has to reach one device.

    ])#agar frontend request aa routes par thi aayi than backend will allow and response to the request else not. aa badhi origin frontend ni che to tell backend that where the API calls and request are coming from.
socketio = SocketIO(app,cors_allowed_origins="*")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'#t means say an user sigs-up than to verify his email and message will be sent in form of email in gmail through secured way through port 587 as google has many ports for difference purposes while 587 it's an secure form or way for google to send any email through this port in secure and enrypted way through TIL and when an user will sign the email will be sent through my gmail that from krishibhavikgnadhi we are verifying you.
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True



app.config['API_KEY'] = os.environ.get('API_KEY')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.secret_key = os.environ.get('APP_SECRET_KEY')
client = razorpay.Client(auth=(os.environ.get('RAZORPAY_TEST_KEY'), os.environ.get('RAZORPAY_SECRET_KEY')))



#initalizing the database:
db.init_app(app)
migrate = Migrate(app, db)  
jwt = JWTManager(app)
mail = Mail(app)#connecting my app with mail server so that i can send mail to user for various purposes like sending them otp for verification, sending them mail for password reset, sending them mail for congratulating them on their investment and many more things.

#check-ups & trial route:
@app.route("/")
def homepage():
    return "Hello World!"


#sign-up routes & pure sign-ups:
@app.route("/user/sign_up/page",methods=['POST'])
def Sign_up():
    data = request.get_json()
    user_data = User.query.filter_by(email = data['email']).first()
    if user_data:
        return jsonify({"message":"The User is already signed in!"}),202
    
    token = secrets.token_urlsafe(32)#generates token for the sign-in user.
    user_data_fill = User(username = data['username'],email =data['email'],verify_token = token,verify_status=False)
    user_data_fill.set_password(data['password'])
    db.session.add(user_data_fill)
    db.session.commit()
    msg = Message('Email Verification',
                  sender='krishibhavikgandhi@gmail.com',
                  recipients=[user_data_fill.email]
                )
    msg.html = f'''
    <!Doctype html>
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; color: #333;">
            <h1>Thanks For sigingin up! for <strong>Demo Fintech App</strong></h1>
            <h3>Please Verify yourself by click the link below:
                <a href="http://192.168.1.4:5173/user/verify_email/{token}" style="display: inline-block; padding: 10px 20px; background-color: #007BFF; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px;">Verify Email</a>         

            </h3>
            <p style="margin-top: 20px;">If you did not sign up for this account, please ignore this email.</p>
            <h4>Thank You!</h4>

        </body>
    </html>
    '''
    mail.send(msg)
    return jsonify({"message":"Check Your Mail", "email":user_data_fill.email}),200 # we before this http://192.168.1.11:5173/user/verify_email/{token} url we wrote localhost but when the user open that link in their devices the phone searches the app in phone and through which the app will open but our app is running on laptop it's not live in the phone so we will connect with the IP address of our wifi network through which when user click the link or requests it will sasys go to this network and at port 5173 and then he will able to see our react page as localhost means run on the smae device while through connecting with IP address we are telling that send tis request to this network and port 5173 and through which the react page will open and then user can see the verification page and click on verify email and then it will send request to backend and backend will verify the token and if it's valid than it will change the verify_status to true in database and send response to frontend that email is verified successfully. 

@app.route("/user/verify_email/<token>",methods=['GET'])
def verify_email(token):
    user = User.query.filter_by(verify_token=token).first()
    if user:
        user.verify_status = True
        
        db.session.commit()
        
        return jsonify({"message":"Email Verified successfully!"}), 200
        
    
    else:
        return jsonify({"message":"Invalid Verification Link"}), 401

#login routes & pure login:
@app.route("/user/log_in/page",methods=['POST'])
def user_login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data.get('password')):
        if user.id == 1:
            user.role = "admin"
            db.session.commit()
            admin_token = create_access_token(identity=(user.email))
            response_1 =  jsonify({"message":"The admin has logged in", "role":user.role})
            set_access_cookies(response_1,admin_token)
            return response_1,200



        if user and (user.check_password(data.get('password')) and user.verify_status == True):


        
            token = create_access_token(identity=(user.email), expires_delta=timedelta(minutes=10))#this sets expiry time of 30 mintes tied to this token now whenever the cookie will arrice with this request checks the expiry and it ends than it will return token expired.
            response = jsonify({"message":"Login Successfully!","role":user.role})
            
            set_access_cookies(response, token)
            return response,200
        # will return this http object to frontend so basically cookie is an short-term memory which browser issue for authenicating request and response when the user make request at login with their details the sqlite verfies user and browser issue cookie with the name auth_token in our case in which the token is wrapped as value of auth_token key than stored it till the user logs-out or cookie expires.
        # so it's basicall sent like body:message, cookie:<token> stored by browser automatically.
        else:
            return jsonify({"message":"Invalid Credentials"}),401
    
    else:
        return jsonify({"message":"User not found or invalid credentials"}),401

#after login the user additional info route:
@app.route("/user/useradditional/info",methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def User_Additional_Info(user,*args,**kwargs):
    data = request.get_json()
    detail_found = UserAdditionalInfo.query.filter_by(users_id=user.id).first()
    
    if detail_found:
        return jsonify({"message":"User additional info already exists"}),200
    
    elif not detail_found:
        marriage_status = data.get('maritialstatus')
        if marriage_status.lower() == 'unmarried':
            unmarried_user_record = UserAdditionalInfo(income=data['income'],
                                             address=data['address'],
                                             city=data['selectedcity'],
                                             state=data['selectedstate'],
                                             nominee=data['nominee'],
                                             occupation=data['occupation'],
                                             earning_members=data['earning_members'],
                                             total_family_members=data['total_family_members'],
                                             blood_relation = data['blood_relation'],
                                             relation_occupation=data['relation_occupation'],
                                             relation_income=data['relation_income'],
                                             pincode=data['pincode'],
                                             age=data['age'],
                                             gender=data['gender'],
                                             family_type = data['family_type'],
                                             maritial_status = data['maritialstatus'],
                                             users_id=user.id,
                                             children=0

                                            )
            
            db.session.add(unmarried_user_record)
            db.session.commit()
            token = create_access_token(identity=(user.email))
            response = jsonify({"message":"User additional info created successfully"})
            set_access_cookies(response,token)
            return response, 200
        elif marriage_status.lower() == 'married':
            married_user_record = UserAdditionalInfo(income=data['income'],
                                                address=data['address'],
                                                city=data['selectedcity'],
                                                state=data['selectedstate'],
                                                nominee=data['nominee'],
                                                occupation=data['occupation'],
                                                earning_members=data['earning_members'],
                                                total_family_members=data['total_family_members'],
                                                blood_relation = data['blood_relation'],
                                                relation_occupation=data['relation_occupation'],
                                                relation_income=data['relation_income'],
                                                pincode=data['pincode'],
                                                age=data['age'],
                                                gender=data['gender'],
                                                maritial_status = data['maritialstatus'],
                                                children = data['no_of_children'],
                                                family_type = data['family_type'],
                                                users_id=user.id
                                                )
            db.session.add(married_user_record)
            db.session.commit()
            token = create_access_token(identity=(user.email))
            response = jsonify({"message":"User additional info created successfully"})
            set_access_cookies(response,token)
            return response, 200
        else:
            return jsonify({"message":"Invalid Method type"}),415
    else:
        return jsonify({"message":"Unauthorized Access"}),401

        
    



#account creation step routes:
@app.route("/user/kyc_submit",methods=["POST"])
@jwt_required(locations=['cookies'])
def kyc_check():
    current_email = get_jwt_identity()
    adhar_file = request.files.get("adhar_file")#this all the key inside which the values are being stored.
    pan_file = request.files.get("pan_file")
    face_file = request.files.get("face_path")
    name = request.form.get("name")
    dob = request.form.get("dob")
    cc = request.form.get("cc")
    phone_num = request.form.get("phone_num")

    
    
    date = datetime.strptime(dob,'%Y-%m-%d')#converts into datetime format.

    current_user = User.query.filter_by(email = current_email).first()
    if current_user:
        kyc_filled = KYC_Model.query.filter_by(user_id = current_user.id).first()
        if not kyc_filled:
            if cc.lower() =='india':
                if pan_file and adhar_file:

                    folder_path = f'kyc_document/user_{current_user.id}'#this creates folder main folder is kyc_document . under which there will be mutiple sub-folder as per user_id
                    os.makedirs(folder_path, exist_ok=True)#os refers to operating systme which helps python to work with our environemnt like it creates files, and folder in our system.
                    #so through the above line we are saying through os.makedirs we the sysmten creates directories/folder so we are saying create an folder name mentioned in the pan_path while through above line we saying
                    #if that named folder already exsits than don't show error that happens becuase of exists_ok=true if we don't write it the python will sjow an filenameerror so writing that is integral.

                    pan_path = f"{folder_path}/pan.jpeg"# this create folder path so here there will be various folder as per user_id while like here filename will be user_2/pan.jpg
                    adhar_path = f"{folder_path}/adhar.jpeg"#same with the adhar card user_2/adhar_card so through which there will no clash or messy folder.
                    face_path = f"{folder_path}/face_img.jpg"
                    #now we will store this path into database while through these we are saving save this image under this folder so image will be saved as kyc_document/user_2/pan.jpg, user_2 s an folder name of that user and which ever document like adhar or pan card will belong to him will saved under this folder with name pan.jpg or adhar.jpg.

                    pan_file.save(pan_path)
                    adhar_file.save(adhar_path)#while we have to seperately write this becuase this save function only add the img to that folder it doesn't return anything so while if we put that statement in database it will be none so we will put pan_path in which whole path will be stored.
                    face_file.save(face_path)
                    
                    ocr_status,ocr_message = verifying_ocr(
                        name=name,
                        dob=dob,
                        pan_path=pan_path,
                        adhar_path=adhar_path,
                        phone_num = phone_num,
                        face_path = face_path
                        
                    )

                    if ocr_status:
                        kyc_filling = KYC_Model(name=name,
                                                phone_num = phone_num,
                                                country_code = cc,
                                                date_of_birth=date,
                                                user_id=current_user.id,
                                                pan_img_path = pan_path,
                                                adhar_img_path = adhar_path,
                                                ocr_status = True,
                                                kyc_status='pending')
                                            
                        db.session.add(kyc_filling)
                        db.session.commit()
                        token = create_access_token(identity=(current_user.email))
                        response = jsonify({"message":"Kyc has been submitted, Verifying you!"})
                        set_access_cookies(response,token)
                        return response,200
                    return jsonify({"message":ocr_message})
                return jsonify({"message":"Pancard and Adhar card is necesssary document!"})
                
            else:
                return jsonify({"message":"You're not valid for account openization!"}),401
        
        elif kyc_filled and kyc_filled.kyc_status == 'pending':
            return jsonify({"message":"You're Kyc is still under verification please wait until we verify you!"}),202
        
        elif kyc_filled and kyc_filled.kyc_status == 'verified':
            return jsonify({"message":"Your kyc is already verified "}),200
        
        
        else:
            return jsonify({"message":"Invalid Credentials!"}),409
    else:
        return jsonify({"message":"Unauthorized User!"}),401



#for account opening sending users_kyc to bank:
@app.route("/request_to_bank_app_by/my_fintech_app",methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def app_to_bank_app(user,*args,**kwargs):
    
    message = app_login()
    if message.get('status') not in [200,202]:
        return jsonify({"message":"Invalid token"}),401
        
    kyc_filter = KYC_Model.query.filter_by(user_id=user.id).first()
    if kyc_filter and kyc_filter.kyc_status == 'verified':
        return jsonify({"message":"Your kyc is already being submitted!"}),202
    elif kyc_filter and kyc_filter.kyc_status == 'pending':
        if kyc_filter and kyc_filter.ocr_status == True:
            kyc_data_to_sent = []
            kyc_data_to_sent.append({
                "kyc_user_id":kyc_filter.id,
                "adhar_file_path":kyc_filter.adhar_img_path,
                "pan_file_path":kyc_filter.pan_img_path,
                "dob":kyc_filter.date_of_birth,
                "ocr_status":kyc_filter.ocr_status
            })
            result = submitting_kyc_form(kyc_data_to_sent)
            if result.get('status') not in [200,202]:
                return jsonify({"message":result.get('message')}),409
            else:
                return jsonify({"message":result.get('message')}),200
        else:
            return jsonify({"message":"Your kyc is being not submitted!"}),404
    
    else:
        return jsonify({"message":"Invalid Response"}),404

#after bank approves than admin approves the account gets create and email will sent route:

@app.route("/user/account_creation",methods=['POST','GET'])
@jwt_required(locations=["cookies"])
@check_current_user
def account_creation(user,*args,**kwargs):
    if request.method == 'POST':
        user_exists = Account.query.filter_by(user_id = user.id).first()
        if user_exists:
            
            token = create_access_token(identity=(user.email))
            account_creation_response = jsonify({"message":"Account Created Successfully!","account_num":user_exists.account_num})
            set_access_cookies(account_creation_response,token)
            return account_creation_response,200
            
        else:
            return jsonify({"message":"Unauthorized User !"}),401
            
    elif request.method == 'GET':
        account_exists = Account.query.filter_by(user_id=user.id).first()
        
        if not account_exists:
            return jsonify({"message":"Account not Exists!"}),401
        elif not account_exists:
            kyc_check = KYC_Model.query.filter_by(user_id=user.id).first()
            if kyc_check:
                return jsonify({"message":"Your account is still under verification!"}),202
            else:
                return jsonify({"message":"Unauthorized Access"}),401
        return jsonify({"message":"Account Exsits"}),200
    else:
        return jsonify({"message":"Invalid Request type!"}),415
    
#after successfull opening of account the otp verification and authentication route:

@app.route("/user/otp_verification",methods=['GET'])
@jwt_required(locations=['cookies'])
def otp_verification():
    current_email = get_jwt_identity()
    
    

    current_user = User.query.filter_by(email = current_email).first()
    
    if current_user:
        if current_user.otp_status == True:
            
            return jsonify({"message":"The otp veirification has completed, verifying you!"}),202

        ocr_status = KYC_Model.query.filter_by(user_id = current_user.id).first()
        if ocr_status and ocr_status.ocr_status == True:
            otp = random.randint(100000,999999)#this will generate an OTP of 6 digit between 10000 -999999 like 456345 and so on.
            otpexpiry = datetime.now().timestamp() +300# while this line means write current date & time now timestamp means converting current data & time into seconds and than add 300 seconds means 5 minutes to that timestamp so together it means calculate timestamp and than add 5 minutes to that timestamp and than we will get the expiry time of the OTP.
            current_user.otp_code = otp
            current_user.otp_expiry = otpexpiry
            current_user.otp_status = True
            db.session.commit()
            token = create_access_token(identity=(current_user.email))
            response = jsonify({"message":"OTP sent to your adhar registered mobile num!", "kyc_id":ocr_status.id})
            set_access_cookies(response, token)


            msg = Message('KYC verification',
                  sender='krishibhavikgandhi@gmail.com',
                  recipients=[current_user.email]
                )
            msg.html = f'''
            <!Doctype html>
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; color: #333;">
                <h1>Thanks For sigingin up! for <strong>Demo Fintech App</strong></h1>
                <h3>Your OTP for KYC verification is: <strong>{otp}</strong></h3>
                <p style="margin-top: 20px;">Please do not share this OTP with anyone.</p>
                <h4>Thank You!</h4>
            </html>
            </body>
                '''
            mail.send(msg)


            
            return response,200
        return jsonify({"message":"OCR verification is not done yet!"}),401
    return jsonify({"message":"Unauthorized User!"}),401

@app.route("/user/otp_authentication",methods=['POST'])
@jwt_required(locations=['cookies'])
def otp_authentication():
    current_email = get_jwt_identity()
    data = request.get_json()

    current_user = User.query.filter_by(email = current_email).first()
    if current_user:
        if current_user.otp_code == data.get('otp'):
            if datetime.now().timestamp() > current_user.otp_expiry:
                return jsonify({"message":"OTP has expired, please request a new one"})
            else:
                token = create_access_token(identity=(current_user.email))
                response = jsonify({"message":"OTP has been verified"})
                set_access_cookies(response,token)
                return response,200
        else:
            return jsonify({"message":"Invalid OTP!"})
    return jsonify({"message":"Unauthorized User!"}),401

@app.route("/user/create_app_password",methods=['POST','PUT'])
@jwt_required(locations=['cookies'])
def create_app_password():
    current_user = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()

        user_exists = User.query.filter_by(email = current_user).first()
        if user_exists:
            account_exists = Account.query.filter_by(user_id=user_exists.id).first()
            if account_exists and account_exists.app_password:
                return jsonify({"message":"The password has already been created"}),202
                
            if account_exists and not account_exists.app_password:
                account_exists.set_password(data.get('passKey'))
                db.session.commit()
                token = create_access_token(identity=(user_exists.email))
                response = jsonify({"message":"The passkey has been created successfully","account_num":account_exists.account_num})
                set_access_cookies(response,token)
                return response, 200
                
            if not account_exists:
                return jsonify({"message":"don't hold account"}),401
            
            
        else:
            return jsonify({"message":"User not exists"}),401
    elif request.method == 'PUT':
        data = request.get_json()

        yes_current_user = User.query.filter_by(email = current_user).first()
        if not yes_current_user:
            return jsonify({"message":"User not exsits"}),401
        yes_account_holder = Account.query.filter_by(user_id = yes_current_user.id).first()
        if not yes_account_holder:
            return jsonify({"message":"Account Not Exists"}),401
        if yes_account_holder and yes_account_holder.check_password(data['app_password']):
            yes_account_holder.set_password(data['updated_pass'])
            db.session.add(yes_account_holder)
            db.session.commit()
            msg = Message('Email Verification',
                  sender='krishibhavikgandhi@gmail.com',
                  recipients=[yes_current_user.email]
                )
            msg.html = f'''
                <!Doctype html>
                <html>
                    <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; color: #333;">
                        <h1>Password Updation Message</h1>


                       
                        <h3>Your password has been updated successfully! </h3>
                        <h4>Thank You!</h4>

                    </body>
                </html>
                '''
            mail.send(msg)
            return jsonify({"message":"Mail Sent successfully"}), 200
            
        else:
            
            return jsonify({"message":"Invalid response"}),401
        
        
    
    else:
        return jsonify({"message":"Invalid Reuqest Type"}),415


@app.route("/user/account_holder",methods=["POST","GET"])
@jwt_required(locations=['cookies'])
@check_current_user
def Account_holders(user,*args,**kwargs):
    
    
    if request.method == "POST":
        data = request.get_json()
    
        
        existing_account = Account.query.filter_by(user_id=user.id).first()
        print("existing_account",existing_account)
        if existing_account and existing_account.check_password(data.get('app_password')):
            print("password",data['app_password'])
            account_token = create_access_token(identity=(user.email))
            response =  jsonify({"message":"Account founded", "account_num":existing_account.account_num, "balance":existing_account.balance})
            set_access_cookies(response, account_token)
                
            return response,200
        else:
            print("password",data['app_password'])
            return jsonify({"message":"Account Not Found!"}),404
        
            

        
        
    elif request.method == "GET":
        if user:
            userinfo = UserAdditionalInfo.query.filter_by(users_id=user.id).first()
            if not userinfo:
                return jsonify({"message":"User additional info not found"}),404
            existing_account = Account.query.filter_by(user_id=user.id).first()
            kyc_status = KYC_Model.query.filter_by(user_id=user.id).first()
            
            
            if existing_account:

                return jsonify({"message":"You already hold account"}),202
            
            elif kyc_status and kyc_status.ocr_status == True:
                return jsonify({"message":"You're KYC verified!"}),202
            
            else:
                return jsonify({"message":"You don't hold account"}),401
            
                
        else:
            return jsonify({"message":"User Not exsits"}),401
    else:
        return jsonify({"Undefined or unsupoorted request"}),415
    




#admin panel:

@app.route("/user/kyc_verfying/<int:kyc_id>",methods=["POST"])#we are passing kyc id through frontend 
@jwt_required(locations=['cookies'])
@admin_required
def kyc_verifying(kyc_id):
    
    kyc_done = KYC_Model.query.filter_by(id=kyc_id).first()
    
    
    if not kyc_done:
        return jsonify({"message":"Unauthorized User"}),401
    elif kyc_done and (kyc_done.bank_approved == True and kyc_done.kyc_status == 'verified'):
        account = Account.query.filter_by(user_id=kyc_done.user_kyc.id).first()
        msg = Message('Account Succession Verification',
                  sender='krishibhavikgandhi@gmail.com',
                  recipients=[kyc_done.user_kyc.email]
                )
        msg.html = f'''
        <!Doctype html>
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; color: #333;">
                <h1>Thanks For Account opening! for <strong>Demo Fintech App</strong></h1>
                <h3>Please Go through your Account Details attach below:
                    <h3>Account Number:{account.account_num}</h3>
                    <h2>IFSC Code: {account.account_ifsc}</h2>
                    <p>Now Please visit the app and create an app password key to maintain app and your security</p>

                </h3>
                <h5>IMP Note: Use this  {temp_pass} as your temporary password to login into your account and create an app password key for your security purpose!</h5>
                <h4>Go toyour profile section -> Click Change Password than update your password</h4>
                
                
                <h4>Thank You!</h4>

            </body>
        </html>
        '''
        mail.send(msg)
        return jsonify({"message":"Email sent successfully!"}),200
        
    result1 = app_login()
    if result1.get('status') not in [200,202]:
        return jsonify({"message":"Invalid Token"}),401
    result = collecting_user_status(kyc_id)
    if result.get('status') not in [200,202]:
        return jsonify({"message":"Invalid Response"}),402
    
    

    kyc_done.kyc_status = 'verified'
    kyc_done.bank_approved = True
    temp_pass = secrets.token_urlsafe(6)
    account_created = Account(account_num=result.get('account_num'),account_ifsc = result.get('account_ifsc'),balance=result.get('balance'),user_id=kyc_done.user_kyc.id,bank_dec_id=result.get('bank_user_id'))
    account_created.set_password(temp_pass)
    db.session.add(account_created)
    db.session.commit()
    return jsonify({"message":"Account has been created successfully!"}),200


@app.route("/user/check_active_or_inactive_status",methods=['GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def active_inactive(user_exists,*args,**kwargs):
    today_date = datetime.now().date()
    days = (today_date - user_exists.last_updated.date()).days

    if days >= 4:
        user_exists.inactive_count += 1
    
        if user_exists.inactive_count >= 5:
            user_exists.accounts[0].acc_status = "Freezed Account"
        else:
            user_exists.accounts[0].acc_status = "Inactive"
    else:
        user_exists.inactive_count = 0
        user_exists.accounts[0].acc_status = "Active"

    db.session.commit()
    token = create_access_token(identity=(user_exists.email))
    response = jsonify({"message":"User Log-In updates","Status":user_exists.accounts[0].acc_status,"count":user_exists.inactive_count})
    set_access_cookies(response,token)
    return response,200

@app.route("/user/pending_kyc_list/records",methods=['GET'])
@jwt_required(locations=['cookies'])
@admin_required
def admin_kyc_list_pending():
    kyc_pending_list = KYC_Model.query.filter_by(bank_approved=False,kyc_status ='pending').all()
    kyc_list = []
    for kyc in kyc_pending_list:
        kyc_list.append({
            "kyc_id":kyc.id,
            "kyc_status":kyc.bank_approved,
            "kyc_pending":kyc.kyc_status

        })
    email = g.current_user
    token = create_access_token(identity=(email))
    response = jsonify({"message":"LIST of pending kyc list", "kyc_list_record":kyc_list})
    set_access_cookies(response,token)
    return response, 200

@app.route("/user/approved_user_list",methods=['GET'])
@jwt_required(locations=['cookies'])
@admin_required
def approved_candidate_list():
    kyc_approved = KYC_Model.query.filter_by(bank_approved=True,kyc_status='verified').all()
    if not kyc_approved:
        return jsonify({"message":"List is empty!"}),404
    kyc_list_proved = []
    for kyc_in in kyc_approved:
        kyc_list_proved.append({
            "kyc_id":kyc_in.id,
            "kyc_status":kyc_in.bank_approved,
            "kyc_approved":kyc_in.kyc_status
        })
    email = g.current_user
    token = create_access_token(identity=(email))#okay so it will be like find kyc_id than foreign key for that kyc_record let's say if it's 1 than user_id is 2 so through backref we will see or find the user_id 2 in user_table and their email?correcT?yes
    response = jsonify({"message":"Approved kyc list", "kyc_list_record":kyc_list_proved})
    set_access_cookies(response,token)
    return response, 200

#all users records route for admin only:

@app.route("/fetching_user_logged_in_users/by_admin_only",methods=['GET'])
@jwt_required(locations=['cookies'])
@admin_required
def admin_only_access():
    users = User.query.all()
    if not users:
        return jsonify({"message":"We couldn't find any user records"}),404
    user_records = []
    for u in users:
        user_records.append({
            "id":u.id,
            "username":u.username,
            "email":u.email,
            "Exists_Or_Not":"Account Exists" if u.accounts else "Account Not Exists!",
            "Has_Account":u.accounts[0].acc_status if u.accounts else "No Account Found!",#why iterating becuase if we only write u.accounts it will return the whole account lists tied to that user but hre we want only acc_status fields or columns for that we are saying get the first account object whic we get through [0] and from that get the status columns only and than the results are being displayed.
            "demat_have":"Account Exists" if u.accounts and u.accounts[0].user_demat else "No Demat Exists!",
            "Investment":"Have Investments" if u.accounts and u.accounts[0].invest_user else "No investments has been made"#so eventually "demat_have": "Demat Exists" if u.account and u.account.user_demat else "No Demat Exists!" here the ID which are foreign keys theat are being checked which is an common factor between this tables and becuase of which these tables are linked
            })
    print("User Record Fetched Successfully!")
    return jsonify({"message":"User records fetched successfully!","u_records":user_records}),200




    
#user dashboard and user Dashboard related routes:
@app.route("/user/dashboard",methods=['GET',"POST"])
@jwt_required(locations=['cookies'])
@check_current_user
def user_dashboard(user,*args,**kwargs):
    account_exists = Account.query.filter_by(user_id=user.id).first()
    if not account_exists:
        return jsonify({"message":"You don't hold account"}),401
    today_date  = date.today()
    todays_transaction = Transaction.query.filter_by(sender_acc=account_exists.account_num,transaction_type='debit').filter(func.date(Transaction.timestamp) == today_date).order_by(Transaction.timestamp.desc()).all()
    
    todays_transaction_data = []
    for transaction in todays_transaction:
        todays_transaction_data.append({
            "timestamp":transaction.timestamp,
            "amount":transaction.amount,
            "transaction_type":transaction.transaction_type,
            "category":transaction.category,
        })

    
    user.last_updated = datetime.utcnow()#this utcnow will store the date and time both at same time
    db.session.commit()
    token = create_access_token(identity=(user.email))
    response = jsonify({"message":"Account Founded", 
                        "account_num":account_exists.account_num,
                        "balance":account_exists.balance,
                        "account_status":account_exists.acc_status,
                        "username":user.username,
                        "acc_type":account_exists.account_type,
                        "user_wallet":user.user_wallet,
                        "last_login_date":user.last_updated.date().isoformat() if user.last_updated else "None",#this isoformat is an converter for datetime objects into string datatypes because except this converter python will not able to convert into json format through which the error will be issued.
                        "last_login_time":user.last_updated.time().isoformat() if user.last_updated else "None",
                        "transaction_data":todays_transaction_data
                        })
    set_access_cookies(response,token)
    return response,200

#add balance route:
@app.route("/user/add_balance_route",methods=['POST','GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def add_balance(user,*args,**kwargs):

    data = request.get_json()
    
    account_exists = Account.query.filter_by(user_id=user.id).first()
    if not account_exists:
        return jsonify({"message":"Account not exists"}),401
    
    deposit_amt = float(data.get('deposit_amt',0.00))
        
    if not deposit_amt:
        return jsonify({"message":"Deposit amount is null"}),400
    if deposit_amt > user.user_wallet:
        return jsonify({"message":"No More balance"}),422
    login = app_login()
    if login.get('status') not in [200,202]:
        return jsonify({"message":"Unauthorized token"}),401
    
    result = bank_add_balance(account_exists.bank_dec_id,deposit_amt,user.user_wallet)
    if result.get('status') not in [200,202]:
        return jsonify({"message":"Balance Cannot be Transferred!","balance":account_exists.balance,"user_wallet":user.user_wallet}),409
    
    account_exists.balance += deposit_amt
    user.user_wallet -= deposit_amt
    db.session.commit()
    token = create_access_token(identity=(user.email))
    response = jsonify({"message":"The balance has been updated successfully","balance":account_exists.balance,"user_wallet":user.user_wallet})
    set_access_cookies(response,token)
    return response,200

#transaction route:
@app.route('/create_order',methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def Transfer_Money(user,*args,**kwargs):
    data = request.get_json()
    try:
        amount= int(data.get('amount')) #raxorpay doesn't understand amount in decimal like 500.00 so we convert it into pasia by mulitplying with 100 500.00 * 100  = 50000 rupees that's why we multiplied with 100 
        amount_in_paisa = amount * 100
        category = data.get('category')
        reciever_acc = data.get('reciever_acc_num')
        sender_acc = data.get('sender_acc_num')
        account1 = Account.query.filter_by(account_num = sender_acc).first()
        account = Account.query.filter_by(account_num=reciever_acc).first()

        if not account1 or not account:
            return jsonify({"message":"Account not found!"}),404
        
        if account.user_id == user.id:
            return jsonify({"message":"you cannot transfer funds to your ownself!"}),409
        
        

        unique_receipt_id = f"REC_{user.id}_{uuid.uuid4().hex[:6]}"#using UUID for generating uniqwue recipt ID per transaction even the same user performs transaction 100 times for each transaction it creates unique recipt id.

        options = {
            "amount": amount_in_paisa,
            "currency":'INR',
            "receipt":unique_receipt_id
        }#this is an object or data which razorpay demands to know the amount demanded and currency and recipt no for database tracking.
        order = client.order.create(data = options)#while becuase of this line when the user clicks on send money the reuqest goes to razorpay server for transaction requests, razorpay verifies our keys like api keys and secret key generated with razorpay and on successfuly verification the razorpay sends the successfuly verification to our backend.
        
        if account1.balance < amount_in_paisa / 100:
            return jsonify({"message":"Insufficent Balance"}),404
        # if not data.get('latitude') and not data.get('longitude'):
        #     pass

        # trax1 = (account1.langitude,account1.longitude)
        # trax2 = (data.get('langitude'),data.get('longitude'))

        # distance = geodesic(trax1,trax2).km #this is an distance which will measure the distance between the two location for ex: if an user-A performs transaction from mumbai at 2:30 and user-A perfroms transaction at 2:45 from delhi than the distance will be mesured how much geopolicital and normally the distance lies between these two cities.

        # time = account1.timestamp - datetime.utcnow()# while this is an time mesure which says what is the difference between transaction performed between revious transaction and current performed transaction, continuing previous example that user-A performs transaction at 2:30 and current transaction which has performed which is let's say 6:20 4 hours that's the time between my two transaction. which also can raise speculation that let's say an user spending from mubai at 2:30 and the same user is spending from delhi at 2:40 the time will be calcualted is 20 minutes which can raise concwrn in 20 mnutes how can person that same person ca travel from mumbai to delhi that's impossible.
        # time_converts_to_hours = time.seconds()/3600#while we have to convert t into hour becuase if we don;t do so it will be broken and give us unpreditable answer or wrong answer than why as in 1 hour there are 3600 seconds now if there an usuakl flight takes 900km/perhour which means an human can maximum travel 900km/in hour not more than that but usually fintech apps takes 1000km/per hour that why we have to take seconds as hour for comparing two same things at a time hour by hour
        # #now 
        # implied_speed = (distance/time_converts_to_hours)# implied_speed means how fastly an user would have traveled to make to transaction happen if it's less than 1000km/h than we will flagged it as green flag else flag as red flag it;s question we are asking like if i want to make this receipe than how much time and cost will needed that's what we are doing it here while implied_speed answer hours seconds like 500km for 0.15 now we have set range which is 1000km/hr if it;s greater than this than it will be flagged as red flag
        # if implied_speed > 1000:
        #     return jsonify({"message":"Transaction Cannot Made"}),401
        
        account1.balance -= amount_in_paisa / 100
        account.balance +=  amount_in_paisa / 100

        debit_record = Transaction(transaction_type='debit',
                                    account_id=account1.id,
                                    status="success",
                                    sender_acc = account1.account_num,
                                    recevier_acc = account.account_num,
                                    category = category,
                                    wallet_ref = order['receipt'],
                                    amount = data.get('amount')
                                    
                                    )
                                            # latitude = data.get('latitude',''),
                                            # longitude = data.get('longitude','')
            
        credit_record = Transaction(transaction_type = "credit",
                                    account_id = account.id,
                                    status ="success",
                                    sender_acc= account1.account_num,
                                    recevier_acc = account.account_num,
                                    category = "Income",
                                    amount = data.get('amount')
                                    )
        
        db.session.add(debit_record)
        db.session.add(credit_record)
        db.session.commit()
        result1 = app_login()
        if result1.get('status') not in [200,202]:
            print("Error",result1)
            return jsonify({"message":"Unauthorized Access"}),401
        passing_dict = {
            "sender_acc":account1.account_num,
            "reciever_acc":account.account_num,
            "amount":amount_in_paisa / 100,
            "wallet_ref":order['receipt']
        }

        result = updation_bal_route(**passing_dict)
        print("🏛️ BANK API RAW RESPONSE:", result)
        if result.get('status') == 404 or result.get('status') == 401 or result.get('status') == 500:
            db.session.rollback()
            return jsonify({"message":"Invalid Response, Balance Has not been updated in thr bank backend!"}),401
        
        return jsonify({"message":"Successfully transferred the amount","order":order,"updated_bal":account1.balance}),200 #while sending that data into frontend
    except Exception as e:
        print("❌ CRITICAL BACKEND ERROR:", str(e)) 
        return jsonify({"message":str(e)}),400

#user transaction history route:
@app.route("/transaction_history",methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def transaction_records(user,*args,**kwargs):
    data = request.get_json()
    if data.get('type') == 'view_transaction':
        account = Account.query.filter_by(user_id=user.id).first()
        if not account:
            return jsonify({"message":"Unauthorized User"}),401
        
        credits_details = Transaction.query.filter_by(account_id=account.id,transaction_type='credit').all()
        
        credits_his = []
        for t in credits_details:
            credits_his.append({
                "transaction_no":t.id,
                "amount":t.amount,
                "transaction_type":t.transaction_type,
                "category":t.category,
                "datetime":t.timestamp,
                "status": t.status
                })
        debits_his = []
        debit_details = Transaction.query.filter_by(account_id=account.id, transaction_type='debit').all()
        for t1 in debit_details:
            debits_his.append({
                "transaction_no":t1.id,
                "amount":t1.amount,
                "transaction_type":t1.transaction_type,
                "category":t1.category,
                "datetime":t1.timestamp,
                "status": t1.status
                })
        
        return jsonify({"message":"Successfully submitted","credit_record":credits_his,"debit_record":debits_his}),200
    elif data.get('type')  == 'filter_transaction':
        account = Account.query.filter_by(user_id=user.id).first()
        if not account:
            return jsonify({"message":"you don't hold account"}),401
        all_category_records = Transaction.query.filter_by(account_id=account.id,category=data['select_cateogry']).all()
        lists = []
        
        for c in all_category_records:
            lists.append({
                "category":c.category,
                "transaction_type": c.transaction_type,
                "date": c.timestamp,
                "amount":c.amount,
                "status":c.status
            })
        return jsonify({"message":"Successfully returned the list","category_records":lists}),200
    elif data.get('type') == 'month_wise':
        account = Account.query.filter_by(user_id=user.id).first()
        if not account:
            return jsonify({"message":"Account Not Found!"}),401
        year = data.get('year')
        month = data.get('month')

        month_start_date = datetime(year,month,1)#here we are converting simple number accepted from frontened to datetime object and as month start date which is actually selected by users which includes year, month, and 1 date of the month so whenever user selects the month we typically takes 1 date of that month and also takes the end day by adding into month and 1st date of that month will be called as or 1 month

        if month == 12:
            month_end_date = datetime(year+1,1,1)#here we are telling that let's say if user select the month 12 decenber as in one year there are only 12 months if user selects the 12 and than end date would be 13 as end date but 13 is not an month nor the same year so that why we are clarifying that when the user slect the the month 12 than take the end date as 1st januaray(1month) and year+1 = 2027 which will count as new year an 1 month and 1 date of that month
        else:
            month_end_date = datetime(year, month+1, 1)#while here we are telling if user selects let's say month = 5 which is may than add one 1 + month = which is 6 ends on 2026,6,1 which completes the 1 month and exclude the first day of feb month which will provide the results till 30th of july till 23:59:59 

        month_records = Transaction.query.filter(Transaction.account_id==account.id,
                                                Transaction.timestamp >= month_start_date,
                                                Transaction.timestamp < month_end_date, #so we are telling here that let's say user select month 1 januaray okay now it will click esle part and add like = 2026,2,1  which will end at feburary 1 date now when we write < end-date we are telling check in the timestamp that there is less than this end_date value which means it will check till 31st janurary 23:59:59 as we are saying it should be less than end_date which says not even 00:00 so that feb -1 partr gets excluded so why 2026,2,1 is excluded becuase users selected he wants to see all his transaction of month januarary he has just slected an month not an date so if user select jauaray than 31st janrary completes the one month and if users slectes with the date like 4th of janurary than how the month is counted 4th janurary to 3rd feburary 2026 that completes the month as januraRY has 31 days total days as per months commits and says when the month gets completed  so for example if user select july 10 thn july has 31 days than we will count the days which should be complete 31 and that ends on 9th of august that's an month
                                                Transaction.transaction_type == 'debit'
                                                ).all()
        if not month_records:
            return jsonify({"message":"Records cannot found!"}),404
        monthly_records = []
        for mr in month_records:
            monthly_records.append({
                "amount":mr.amount,
                "transaction_type":mr.transaction_type,
                "category":mr.category,
                "status":mr.status,
                "timestamp":mr.timestamp
            })
        debit_total = sum(d.amount for d in month_records if d.transaction_type == "debit")
        # credit_total = sum(d.amount for d in month_records if d.transaction_type == "credit")

        #pie chart
        pie_chart_data = db.session.query(# we are using session.query becuase is an flexible way to calcualte and work for aggregated and grouping values i mean when we write transaction.query it filter inside that particular table and find s the whole row but when we want to perform grouping or wrk on aggregated data we use db.session who will directly query database and watch for the values we want from that tables 
            Transaction.category.label('category'),#happens-3 than this happens where group categroy names are being desinged inan group which says return the group_by dairy ,skincre,beverages as a column with name category and their summed up value with the name amoun
            func.sum(Transaction.amount).label('total_amount')
        ).filter(#happens-1
            Transaction.account_id == account.id,#what happens is filter the rows as mentioned month s & e date and rows with debit only type okay that's all
            Transaction.timestamp >= month_start_date,
            Transaction.timestamp < month_end_date,
            Transaction.transaction_type == "debit"
        #transaction.category.label('categroy') looks inside row 1 and 3 of actuall transaction mode's category table their they see the nameis skincare and takes that put that category name label on that so group_by gives the rows which has been collapsed while transaction.categry actaully goes into that category name see which value or name is their and fetch that
        ).group_by(#happens-2
            Transaction.category#than after filtering the grouping happens where skincare against it price [10,30,67] like this while group by drop by duplicates than group category with it's multiple amount not yet summed
        )
        pie_data = []
        for p in pie_chart_data:
            pie_data.append({
                "category":p.category,
                "amount":p.total_amount
            })



        #line chart data :
        line_chart_data = db.session.query(
            func.date(Transaction.timestamp).label('day'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= month_start_date,
            Transaction.timestamp < month_end_date,
            Transaction.transaction_type == 'debit'
        ).group_by(
            func.date(Transaction.timestamp)
        ).all()
        if not line_chart_data:
            return jsonify({"message":"data is empty","list":[]}),404
        chart_data = []
        for l in line_chart_data:
            chart_data.append({
                "day":l.day,
                "total_amount":l.total_amount #on label baiss we return this or call this value
            })




        return jsonify({"message":"Successfully delivered","month_record":monthly_records,"debit_total":debit_total,"chart_data":chart_data,"pie_data":pie_data}),200
    
    elif data.get('type') == 'date_wise':
        account = Account.query.filter_by(user_id=user.id).first()
        if not account:
            return jsonify({"message":"Account Not Found!"}),401
        datee = data.get('StartDate')
        start_date = datetime.strptime(datee,'%Y-%m-%d')#will convert string to datetime but for converting datetime to string we will use strftime like datee.strftime('%Y-%m-%d').
        #now adding timedelta becuase let's say an user selects timeframe between 20-07-26 to 20-07-26 now the transaction are being diclosed is till 00:00 12 clock of midnight of the sameday which is just the starting of the day so mostly it will exclude the whole day transaction records and only transactions performed at exact 12:00 will be last recorded so adding another whole day we are making sure that whole 20th date from 12;00 to 21st 12:00 the transaction records gets disclosed.
        end_date = start_date + timedelta(days=1)#now here why we have not added timedelta to start date only so timedelta adds the one + value current to now so let's say today is 1 than while adding timedelta (days=1) it will give us 2 so when we put this or add this to start date what user actually ask for 1 date transaction log but he is getting 2-nd date transaction log that's bug so that's why we had taken the end date saying show me the record of whole 1 date so even if user enters 1 than he will able to see the data of 1st date only okay so even when we take input from user like start_date , end date? to show them records between this day in start date we take say like 1st date and end date is 15 that means user wants to see records from 1st date to 15th date records now here we will use the before wala start and end logic where swe took both start and end and on end date we had just added timedelta so that users can see the whole transaction data for the date 15 here in the end we added timedelta(1) which stands and means the same as now that takes one full day that's takes 15 full till 23:59:59 not even 16th 00:00 it gets excluded so we added timedetla so it calculate the 15 whole day ptherwise it will gove the result till 14th and exclude the 15th which is not user wants
        lists = []
        view_records = Transaction.query.filter(Transaction.account_id == account.id,
                                                Transaction.timestamp >= start_date,
                                                Transaction.timestamp < end_date,
                                                Transaction.transaction_type == 'debit'
                                                ).all()#in sqlalchemy we will always use , in filter and filter_by and sqlalchemy doesn'r understand his operations as it is python thing so yaa.
        if not view_records:
            return jsonify({"message":"We could not found transaction history for that sepcific date please verify the date"}),404
        for record in view_records:
            lists.append({
                "amount":record.amount,
                "transaction_type":record.transaction_type,
                "category":record.category,
                "status":record.status,
                "timestamp":record.timestamp
        })
        debit_sum = sum(d.amount for d in view_records if d.transaction_type == 'debit')
        # credit_sum = sum(i.amount for i in view_records if i.transaction_type == 'credit')
        return jsonify({"message":"Success","date_wise_records":lists,"debit_total":debit_sum}),200
    
    elif data.get('type') == 'year_wise':
        account = Account.query.filter_by(user_id=user.id).first()
        if not account:
            return jsonify({"message":"Unauthorized User"}), 401

        year = int(data.get('selectyear'))
        year_start_date = datetime(year, 1, 1)#user_entered_year let's say 2026 will take month 1 and date 1 and end date will be 2026 + 1 which means it will take  < than 2027,1,1 we added +1 here becuase we are saying when user select 2026 and end 2026 + 1  = 2027 if we don't do these +1 which says where to stop so without +1 we are giving start and end same 2026,2026 now whe we put the condition that timestamp >= year thst mesns year which is selected by user should be >= now it's equals to 2026 now for the end we are saying it should be less than 2026 than means if we take 2026 as start and 2026 as ending so beofre even eaching heading towards 2026 00:01 it will stop and return empty lists  as there is no range only between these year so that why we do +1 which will exclude the 2027 1,1 but include the whole 2026 year
        year_end_date = datetime(year + 1, 1, 1)

        find_transaction = Transaction.query.filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= year_start_date,
            Transaction.timestamp < year_end_date,
            Transaction.transaction_type == 'debit'
        ).order_by(Transaction.timestamp.asc()).all()#without these order_by the records presentation will not be done correctly that's why we have written these else there is nothing to do here for logic or anything else

        if not find_transaction:
            return jsonify({"message":"Transaction Not found!"}),404

        lists = []
        for t in find_transaction:
            lists.append({
                "transaction_type":t.transaction_type,
                "amount": t.amount,
                "category": t.category,
                "date": t.timestamp,
                "status": t.status
                
            })

        debit_sum = sum(d.amount for d in find_transaction if d.transaction_type == 'debit')
        # credit_sum = sum(i.amount for i in find_transaction if i.transaction_type == 'credit')

        year_line_chart = db.session.query(
            func.strftime('%m',Transaction.timestamp).label('month'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= year_start_date,
            Transaction.timestamp < year_end_date,
            Transaction.transaction_type == 'debit'
        ).group_by(
            func.strftime('%m',Transaction.timestamp)#func.strftime('%m', Transaction.timestamp).label('month')so this func.strftime will fetch the month and convert it into string format from the transaction.timestamp so always remember that whenever we want to fetch the month from the timstamp column the func.stftime fetches the month  i mean firstly they will convert the datetime into string and than fetches out month in string format.
        )
        if not year_line_chart:
            return jsonify({"message":"Transaction data not found!"}),404
        yearly_data = []
        for y in year_line_chart:
            yearly_data.append({
                "month":y.month,
                "amount":y.total_amount
            })

        yearly_pie_data = db.session.query(
            Transaction.category.label('category'),#Transaction.category in the SELECT → not scanning individual rows anymore. It’s just pulling the group’s category value.
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= year_start_date,
            Transaction.timestamp < year_end_date,
            Transaction.transaction_type == 'debit'
        ).group_by(
            Transaction.category
        )

        if not yearly_pie_data:
            return jsonify({"message":"Success","data":[]}),404
        pie_data = []
        for data in yearly_pie_data:
            pie_data.append({
                "category":data.category,
                "amount":data.total_amount
            })




        return jsonify({
            "message": "Success",
            "year_wise_records": lists,
            "debit_total": debit_sum,
            
            "yearly_data":yearly_data,
            "pie_datas":pie_data
        }), 200
        
            

    else:
        return jsonify({"message":"Invalid Type"}),415
   


#here we are creating a route which will provide the year list from the first transaction date to current year so that user can select the year and see the transaction history of that year.
@app.route("/user/transaction_datetime",methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def year_calender(user,*args,**kwargs):

    account = Account.query.filter_by(user_id=user.id).first()
    if not account:
        return jsonify({"message":"Account not found!"}),401
    transaction_year = Transaction.query.filter_by(account_id=account.id)\
                    .order_by(Transaction.timestamp.asc()).first() #here firstly we are sequencing transaction data into sorted way like old transaction date first and current r recently or lastest transaction added lastly so yaa through order by we are sorting them 
                #while \ refers to nothing here but integral to keep or write becuase it says the condition orderby is in continuion condition not an seperate to aviod error or buugs
    if not transaction_year:
        return jsonify({"message":"Record not found", "years":[]}),404

    start_year = transaction_year.timestamp.year#2026
    current_year = datetime.utcnow().year

    years = list(range(start_year,current_year+1))#this +1 here is different and completely different topic and logic compared to previous date one logic here we are using range where we mention start,end,step the same way we have done that too here we said start with 2026 first record to current now that current + 1 which will store 2027 but as we know range shows and adds or consider the number before that end number [2026,2026] if we write like these than range will send [] list as we know 2026 will not be count but when we write 2026,2027 than it will easily give us the 2026 record only by excluding 2027.
    return jsonify({"message":"Successfully send year list","years":years}),200



    

    

    


    

#Investment and live market routes:
#first we will check that demat exists or not on demat creation request from user:
@app.route("/user/check_demat_exists",methods=['GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def demat_exists(user_exists,*args,**kwargs):
    account_id = Account.query.filter_by(user_id=user_exists.id).first()

    if not account_id:
        return jsonify({"message":"The account not exists!"}),401
    demat_there = DematAccount.query.filter_by(account_id = account_id.id).first()
    if demat_there:
        return jsonify({"message":"Demat Account already exists"}),200
    return jsonify({"message":"The demat not exists"}),401


#here we are creating an idneity check route for demat account creation where user will be asked to verify his identity through otp verification and after that he will be able to create demat account.
@app.route("/user/create_demat_acc",methods=['POST','GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def create_demat_account(user,*args,**kwargs):
    if request.method == 'GET':
        account_exists = Account.query.filter_by(user_id=user.id).first()
        if not account_exists:
            return jsonify({"message":"account not found!"}),401
        
        demat_exists = DematAccount.query.filter_by(account_id=account_exists.id).first()
        if not demat_exists:
            return jsonify({"message":"Demat Not exists!"}),401
        else:
            return jsonify({"message":"Already hold account"}),202
        
    elif request.method == 'POST':
        kyc_done = KYC_Model.query.filter_by(user_id=user.id).first()
            
        if kyc_done and kyc_done.kyc_status == 'verified':
            account = Account.query.filter_by(user_id=user.id).first()
            
            if not account:
                return jsonify({"message":"You don't hold account"}),401
            
            
            otp = random.randint(19000,39000)
            session['otp_enter'] = otp
            session['otp_expiries'] = datetime.now().timestamp() + 300
                
            msg = Message('OTP Verification',
                            sender='krishibhavikgandhi@gmail.com',
                            recipients=[user.email]
                            )
            
            msg.html = f'''
                <!Doctype html>
                    <html>
                        <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; color: #333;">
                            <h1>Your OTP! for <strong>Demat Account</strong></h1>
                            <h3>Please Verify yourself by click the link below:
                                <h2 style="display: inline-block; padding: 10px 20px; background-color: #007BFF; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px;">{otp}</h2>         

                            </h3>
                            <p style="margin-top: 20px;">Please don't share this OTP with anyone</p>
                            <h4>Thank You!</h4>

                        </body>
                    </html>
                    '''
            mail.send(msg)
            token = create_access_token(identity=(user.email))
            response = jsonify({"message":"Please Verify Your identity!","account_num":account.account_num, "username":user.username,"kyc_status":kyc_done.kyc_status})
            set_access_cookies(response,token)
            return response, 200
        else:
            return jsonify({"message":"Your Kyc verification is still not done!"}),401
    else:
        return jsonify({"message":"Invalid Request type!"}),405

#demat account approved by bank:
@app.route("/user/new_demat_record",methods=['POST','GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def insert_demat_record(user_exists,*args,**kwargs):
    data = request.get_json()
    account = Account.query.filter_by(user_id=user_exists.id).first()
    otp = int(data.get('otp'))
    if not account:
        return jsonify({"message":"Account not found!"}),401
    result1 = app_login()
    if result1.get('status') not in [200,202]:
        return jsonify({"message":"Unauthorized Access"}),401
        
    result = demat_acc_approval(account.bank_dec_id)
    if result.get('status') not in [200,202]:
        return jsonify({"message":"Unauthorized Access"}),401
    
    if session.get('otp_enter') == otp and datetime.now().timestamp() < session.get('otp_expiries'):
        new_dmt_acc = DematAccount(account_id=account.id,bank_approval=result.get('bank_status'),dem_account_id=result.get('demat_id'))
        db.session.add(new_dmt_acc)
        db.session.commit()
        token = create_access_token(identity=(user_exists.email))
        response = jsonify({"message":"Demat Account opened successfully!"})
        set_access_cookies(response,token)
        return response,200
    else:
        return jsonify({"message":"Invalid Credentials!"}),409

    
    
#stock data route:

def get_live_stock_data(stripe):
    
    
    stock = yf.Ticker(f"{stripe}.NS")#extract the mentioned company stocks data

    data = stock.history(period="1d", interval="1m")#here we are saying show me 1 day minute-minute change of stocks price movements
    if data.empty:
        return "Data not found",409
    lastest = data.tail(1)#today's lastest price changed for that company provide me that while row
    
    return {
        'price':float(lastest['Close'].values[0]),#picking the closed priced of the day on which the stock was traded last 
        'volatality':round(lastest['High'].values[0] - lastest['Low'].values[0].min(),2)#while the price shows the current price and this volatality shows as the number increases the volatality in minutes is increased and that called extremem volatality for ex: the high is 50 and low is 10 the difference 40 that means average volatality if the difference is 5 that means smooth and as it number rises it shows volatality condition in an minute.
    }


#used web socket to provide the live market updates to the users who are connected to the socket network and they can see the live market updates of the company they have selected.
active_stock = {}
@socketio.on('check_market_updates')
@jwt_required(locations=['cookies'])
def live_market_updates(data):
    stripe = data.get("stripe").upper().strip()
    if not stripe:
        return jsonify({"message":"Stripe is empty"}),401
    sid = request.sid #an key of generated secret-key to identity the user so what happens is when the client connect to socket-io network the browser creates an key for that specific user and that password is store as key with the value which consists the company name so let's say user-1 connect to socket network the network or browser creates an passkey which will help socket to recognise from where the rerquest is coming so we are storing that passkey as sid in active and value will be the company name which will eb stored against their passkey so let's say user-1 first sleects RELIANCE than user-1 slects Bajajfinace so the key remain save which will be recognised and the only company name changes.
    active_stock[sid] = stripe#company name as value to their connection passkey.
    print(f"sid:{sid}, stripe:{stripe}, active_stock{active_stock}")
    
    

    while True:
        if active_stock.get(sid) != stripe:
            print(f"sid:{sid}, stripe:{stripe}, active_stock{active_stock}")
            break
        
        data = get_live_stock_data(stripe)

            
        socketio.emit('market_update',data,room=sid)#while this room refers to it tells sid to whom to show the company's price which directly cut to show all the people who are connected to the network. through room we are saying provide this information to those to whom it belongs or who it request instead of broadcasting t every client connected to this socket network.
            #emit here the commentory person who speaks every 5 seconds the updated scores while inside it the data is there price and volatality and return as data with message to the app users market update or any name we want to keep.
        socketio.sleep(5)#the seconds we want in how much second the updates you want .
   
@app.route("/user/Buy_Stock",methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def buy_sell_stock(user_exists,*args,**kwargs):
    data = request.get_json()
    
    account_have = Account.query.filter_by(user_id=user_exists.id).first()
    if not account_have:
        return jsonify({"message":"User don't hold account"}),401
    demat_there = DematAccount.query.filter_by(account_id=account_have.id).first()
    if not demat_there:
        return jsonify({"message":"user don't hold demat"}),401
    if data.get('type') == 'Buy':
        price = data.get('current_price')
        quantity = data.get('quantity')
        totalPrice = price * quantity
        user_holds = DematHoldings.query.filter_by(user_investments=account_have.id,stock_name =data.get('company')).first()
        if not user_holds:
            
            if totalPrice > account_have.balance:
                return jsonify({"message":"Insufficient Balance!"}),404
            account_have.balance -= totalPrice
            new_stock_holding = DematHoldings(stock_name = data['company'],quantity=quantity,buy_price = totalPrice ,user_investments=account_have.id)
            db.session.add(new_stock_holding)
            db.session.commit()
            token = create_access_token(identity=(user_exists.email))
            response = jsonify({"message":"The order has been placed successfully!","updated_balance":account_have.balance})
            set_access_cookies(response,token)
            return response,200
        if user_holds and account_have.balance > totalPrice and account_have.balance - totalPrice < 100:
            account_have.balance -= totalPrice
            user_holds.buy_price += totalPrice
            user_holds.quantity += quantity
            db.session.commit()
            return jsonify({"message":"Order has been placed!","updated_balance":account_have.balance}),200
        
        
        else:
            return jsonify({"message":"Got an invalid response or requests"}),409
        
    elif data.get('type') == 'Sell':
        sell_quantity = data.get('quantity')
        price = data.get('current_price')
        holds_or_not = DematHoldings.query.filter_by(user_investments = account_have.id, stock_name=data['company']).first()
        if not holds_or_not:
            return jsonify({"message":"You don't hold this share!"}),401
        if holds_or_not and holds_or_not.quantity >= sell_quantity:
            avg_price = holds_or_not.buy_price / holds_or_not.quantity #find or calcualtes the average price which says on an average how much you gained per share let's say an average comes out 5 than on each share you gained 5 rupee averagely which shows and used only for showing the user how much he gained on an average from his investment.
            returns = (price - avg_price) * sell_quantity #this explain let's say and today price is 100 each for one share and avg price is 200 than we subtract we get 100 * quantity say 50 5000 is the acutal returns you gained on 50 shares total while the previous one show or calcualte the profit or average price of one share while this shows accumulated profit
            holds_or_not.buy_price -= avg_price * sell_quantity # here we are showing and subtracting that after deducting how much total investment is being there.
            holds_or_not.quantity -= sell_quantity
            account_have.balance += price * sell_quantity #while in the balance the thing which only go is current price of that share and quantity he wants to sell
            db.session.commit()
            token = create_access_token(identity=(user_exists.email))
            response = jsonify({"message":"The sell order has been placed successfully!","updated_balance" :account_have.balance,"accumulated_returns":returns,"avg_price":avg_price,"total_investment":holds_or_not.buy_price,"updated_quantity":holds_or_not.quantity })
            set_access_cookies(response,token)
            return response,200
        else:
            return jsonify({"message":"Not enough Quantity "}),401
    else:
        return jsonify({"message":"Invalid type!"}),404



@socketio.on('disconnect')
def handle_disconnect():
    active_stock.pop(request.sid , None)# this will remove and clean up the delted things clearly so it run smoothly.

#only company list route:
@app.route("/user/fetching_company_list",methods=['GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def company_list(user_exists,*args,**kwargs):
    company_lists = fetching_50_companies()
    
    lists = list(company_lists.keys())
    return jsonify({"message":"Company_lists Founded!", "list":lists}), 200


#company list with timeframe and their price data route:
@app.route("/user/select_the_company",methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def get_company_lists(user_exists,*args,**kwargs):
    account_exists = Account.query.filter_by(user_id=user_exists.id).first()

    data = request.get_json()
    timeframe = data.get('timeframe')

    symbol = data.get('company')
    if not account_exists:
        return jsonify({"message":"You don't have account"}),401
    
    symbol_data = fetching_50_companies()
    
    key_value = []

    if symbol in symbol_data and timeframe in symbol_data[symbol]:
        key_value = symbol_data[symbol][timeframe]
        return jsonify({
            "message": "Data has been processed",
            "data": key_value,
            "updated_balance":account_exists.balance
        }), 200
            
    return jsonify({
                "message":"Data not founded!",
                "data":[]
                
                }),404

#user investment portfoilio:
@app.route("/user/investment_portfolio",methods=['GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def investment_portfolio(user_exists,*args,**kwargs):
    
    account_there = Account.query.filter_by(user_id=user_exists.id).first()
    if not account_there:
        return jsonify({"message":"Account not found!"}),401
    
    investments = []
    demat_holdings = DematHoldings.query.filter_by(user_investments=account_there.id).all()
    if not demat_holdings:
        return jsonify({"message":"You don't hold any investments!"}),404
    current_price = fetching_current_price([i.stock_name for i in demat_holdings])
    if current_price is None:
        return jsonify({"message":"Current price not found!"}),404
    
    price_lookup_in_dict = {item["company"]: item["current_price"] for item in current_price}

        
    
    for i in demat_holdings:
        fetch_stock_price = price_lookup_in_dict.get(i.stock_name)
        if fetch_stock_price is None:
            return jsonify({"message":"Current price not found!"}),404
        
        investments.append({
            "investment_id":i.id,
            "company_name":i.stock_name,
            "buy_price":i.buy_price,
            "quantity":i.quantity,
            "date":i.buy_date.strftime("%Y-%m-%d"),
            "current_price":fetch_stock_price * i.quantity
            

        })

    
    portfolio_value = sum(item["current_price"] for item in investments)
    token = create_access_token(identity=(user_exists.email))
    response = jsonify({"message":"Investment Portfolio","investments":investments, "portfolio_value":portfolio_value})
    set_access_cookies(response,token)
    return response,200

#investment history by tracking and extracting the sector name :
@app.route("/user/get_sector_name",methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def getting_sector_based_price(user_exists,*args,**kwargs):
    account_exists = Account.query.filter_by(user_id=user_exists.id).first()
    if not account_exists:
        return jsonify({"message":"Account not exists!"}),401
    user_investments = DematHoldings.query.filter_by(user_investments=account_exists.id).all()
    if not user_investments:
        return jsonify({"message":"There is not investments has been done"}),401
    
    data = identify_the_sector(user_investments)

    if data is None:
        return jsonify({"message":"Data is empty!"}),404
    token = create_access_token(identity=(user_exists.email))
    response = jsonify({"message":"The data has founded successfully","data":data})
    set_access_cookies(response,token)
    return response,200

# @app.route("/user/check_user_credentials",methods=['POST'])
# @jwt_required(locations=['cookies'])
# @check_current_user
# def check_user_credentials(user_exists,*args,**kwargs):
#     data = request.get_json()
#     if data.get('hasAccount') == 'yes' and data.get('kycVerified') == 'yes':
#         account_exists = Account.query.filter_by(user_id=user_exists.id).first()
#         if not account_exists:
#             return jsonify({"message":"Account not found!"}),401
#         token = create_access_token(identity=(user_exists.email))
#         response = jsonify({"message":"User has account and kyc verified!","account_num":account_exists.account_num,"name":user_exists.username,"kyc_status":"verified"})
#         set_access_cookies(response,token)
#         return response,200
#     else:
#         return jsonify({"message":"User don't have account or kyc not verified!"}),401




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


