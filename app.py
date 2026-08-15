
from flask import Flask, jsonify, request,g,session
from extensions import db
from models import User, Account, Transaction, KYC_Model,DematHoldings,DematAccount,UserAdditionalInfo
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, set_access_cookies
import yfinance as yf
from flask_cors import CORS
import razorpay
import uuid
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
from bank_connection import app_login,submitting_kyc_form,collecting_user_status,updation_bal_route,demat_acc_approval
import requests
import os
from dotenv import load_dotenv
from geopy.distance import geodesic
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
   

    ])
socketio = SocketIO(app,cors_allowed_origins="*")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_SUPPRESS_SEND'] = False

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
mail = Mail(app)



    
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
    
    token = secrets.token_urlsafe(32)
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
                <a href="http://localhost:5173/user/verify_email/{token}" style="display: inline-block; padding: 10px 20px; background-color: #007BFF; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px;">Verify Email</a>         

            </h3>
            <p style="margin-top: 20px;">If you did not sign up for this account, please ignore this email.</p>
            <h4>Thank You!</h4>

        </body>
    </html>
    '''
    try:
        with mail.connect() as conn:
            conn.send(msg)
    except Exception as e:
        print(f"Email sending failed: {e}")
    
    return jsonify({"message":"Check Your Mail", "email":user_data_fill.email}),200 


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


        
            token = create_access_token(identity=(user.email), expires_delta=timedelta(minutes=10))
            response = jsonify({"message":"Login Successfully!","role":user.role})
            
            set_access_cookies(response, token)
            return response,200
        
        else:
            return jsonify({"message":"Invalid Credentials"}),401
    
    else:
        return jsonify({"message":"User not found or invalid credentials"}),401

#after login the user additional info route:
@app.route("/user/useradditional/info",methods=['POST','GET'])
@jwt_required(locations=['cookies'])
@check_current_user
def User_Additional_Info(user,*args,**kwargs):
    
    if request.method == 'POST':
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
        
        
        
    elif request.method == 'GET':
        userinfo = UserAdditionalInfo.query.filter_by(users_id=user.id).first()
        if not userinfo:
            return jsonify({"message":"User Info not Founded"}),401
        return jsonify({"message":"User FOunded"}),200
    
    else:
        return jsonify({"message":"Invalid Type"}),415
    
    
#account creation step routes:
@app.route("/user/kyc_submit",methods=["POST"])
@jwt_required(locations=['cookies'])
def kyc_check():
    current_email = get_jwt_identity()
    adhar_file = request.files.get("adhar_file")
    pan_file = request.files.get("pan_file")
    face_file = request.files.get("face_path")
    name = request.form.get("name")
    dob = request.form.get("dob")
    cc = request.form.get("cc")
    phone_num = request.form.get("phone_num")

    
    
    date = datetime.strptime(dob,'%Y-%m-%d')

    current_user = User.query.filter_by(email = current_email).first()
    if current_user:
        kyc_filled = KYC_Model.query.filter_by(user_id = current_user.id).first()
        if not kyc_filled:
            if cc.lower() =='india':
                if pan_file and adhar_file:

                    folder_path = f'kyc_document/user_{current_user.id}'
                    os.makedirs(folder_path, exist_ok=True)
                    

                    pan_path = f"{folder_path}/pan.jpeg"
                    adhar_path = f"{folder_path}/adhar.jpeg"
                    face_path = f"{folder_path}/face_img.jpg"
                    

                    pan_file.save(pan_path)
                    adhar_file.save(adhar_path)
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
            otp = random.randint(100000,999999)
            otpexpiry = datetime.now().timestamp() +300
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
        if existing_account and existing_account.check_password(data.get('app_password','').strip()):
            print("password Matched",data['app_password'])
            account_token = create_access_token(identity=(user.email))
            response =  jsonify({"message":"Account founded", "account_num":existing_account.account_num, "balance":existing_account.balance})
            set_access_cookies(response, account_token)
                
            return response,200
        else:
            print("password Mismatched",data['app_password'])
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

@app.route("/user/kyc_verfying/<int:kyc_id>",methods=["POST"])
@jwt_required(locations=['cookies'])
@admin_required
def kyc_verifying(kyc_id):
    
    kyc_done = KYC_Model.query.filter_by(id=kyc_id).first()
    
    
    if not kyc_done:
        return jsonify({"message":"Unauthorized User"}),401
    
    elif kyc_done and kyc_done.kyc_status == 'verified':
        return jsonify({"message":"Already KYC Verified "}),202
    
    elif kyc_done.bank_approved == True and kyc_done.kyc_status == 'verified':
        account = Account.query.filter_by(user_id=kyc_done.user_kyc.id).first()
        temp_pass = secrets.token_urlsafe(6)
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
    token = create_access_token(identity=(email))
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
            "Has_Account":u.accounts[0].acc_status if u.accounts else "No Account Found!",
            "demat_have":"Account Exists" if u.accounts and u.accounts[0].user_demat else "No Demat Exists!",
            "Investment":"Have Investments" if u.accounts and u.accounts[0].invest_user else "No investments has been made"
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
    todays_investments = DematHoldings.query.filter_by(invest_type='buy').filter(func.date(DematHoldings.buy_date) == today_date).order_by(DematHoldings.buy_date.desc()).all()
    todays_transaction = Transaction.query.filter_by(sender_acc=account_exists.account_num,transaction_type='debit').filter(func.date(Transaction.timestamp) == today_date).order_by(Transaction.timestamp.desc()).all()
    
    todays_transaction_data = []
    for transaction in todays_transaction:
        todays_transaction_data.append({
            "entry_type":"transactions",
            "timestamp":transaction.timestamp,
            "amount":transaction.amount,
            "transaction_type":transaction.transaction_type,
            "category":transaction.category
           
        })
    
    for invest in todays_investments:
        todays_transaction_data.append({
            "entry_type":"investments",
            "stock_name":invest.stock_name,
            "amount":invest.buy_price * invest.quantity,
            
            "timestamp":invest.buy_date,
            "quantity":invest.quantity
        })
    todays_transaction_data.sort(key=lambda x: x["timestamp"], reverse=True)

    tranx = sum([i.amount for i in todays_transaction if i.transaction_type == 'debit'])
    invests = sum([s.buy_price*s.quantity for s in todays_investments if s.invest_type == 'buy'])
    today_spent = tranx + invests

    
    user.last_updated = datetime.utcnow()
    db.session.commit()
    token = create_access_token(identity=(user.email))
    response = jsonify({"message":"Account Founded", 
                        "account_num":account_exists.account_num,
                        "balance":account_exists.balance,
                        "account_status":account_exists.acc_status,
                        "username":user.username,
                        "acc_type":account_exists.account_type,
                        "last_login_date":user.last_updated.date().isoformat() if user.last_updated else "None",
                        "last_login_time":user.last_updated.time().isoformat() if user.last_updated else "None",
                        "transaction_data":todays_transaction_data,
                        "today_spend":today_spent
                        
                        })
    set_access_cookies(response,token)
    return response,200



#transaction route:
@app.route('/create_order',methods=['POST'])
@jwt_required(locations=['cookies'])
@check_current_user
def Transfer_Money(user,*args,**kwargs):
    data = request.get_json()
    try:
        amount= int(data.get('amount'))
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
        
        

        
        
        if account1.balance < amount_in_paisa / 100:
            return jsonify({"message":"Insufficent Balance"}),404
        
        
        account1.balance -= amount_in_paisa / 100
        account.balance +=  amount_in_paisa / 100

        debit_record = Transaction(transaction_type='debit',
                                    account_id=account1.id,
                                    status="success",
                                    sender_acc = account1.account_num,
                                    recevier_acc = account.account_num,
                                    category = category,
                                    
                                    amount = data.get('amount')
                                    
                                    )
                                                        
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
            "wallet_ref":debit_record.id,
            "sender_bal":account1.balance,
            "receiver_bal":account.balance
            
        }
        

        result = updation_bal_route(**passing_dict)
        print("🏛️ BANK API RAW RESPONSE:", result)
        if result.get('status') == 404 or result.get('status') == 401 or result.get('status') == 500:
            db.session.rollback()
            return jsonify({"message":"Invalid Response, Balance Has not been updated in thr bank backend!"}),401
        
        return jsonify({"message":"Successfully transferred the amount","updated_bal":account1.balance,"transaction_id":debit_record.id}),200 #while sending that data into frontend "order":order,
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
        credit_invests = DematHoldings.query.filter_by(user_investments=account.id,invest_type='sell').all()
        credits_details = Transaction.query.filter_by(account_id=account.id,transaction_type='credit').all()
        
        credits_his = []
        for t in credits_details:
            credits_his.append({
                "entry_type":"transactions",
                "transaction_no":t.id,
                "amount":t.amount,
                "transaction_type":t.transaction_type,
                "category":t.category,
                "datetime":t.timestamp,
                "status": t.status
                })
        for t2 in credit_invests:
            credits_his.append({
                "entry_type":"investments",
                "stock_name":t2.stock_name,
                "amount":t2.buy_price * t2.quantity,
                "timestamp":t2.buy_date,
                "quantity":t2.quantity
            })
        debits_his = []
        debit_details = Transaction.query.filter_by(account_id=account.id, transaction_type='debit').all()
        debit_invest = DematHoldings.query.filter_by(user_investments=account.id,invest_type='buy').all()
        for t1 in debit_details:
            debits_his.append({
                "entry_type":"transactions",
                "transaction_no":t1.id,
                "amount":t1.amount,
                "transaction_type":t1.transaction_type,
                "category":t1.category,
                "datetime":t1.timestamp,
                "status": t1.status
                })
        for i in debit_invest:
            debits_his.append({
                "entry_type":"investments",
                "stock_name":i.stock_name,
                "amount":i.buy_price * i.quantity,
                "timestamp":i.buy_date,
                "quantity":i.quantity
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

        month_start_date = datetime(year,month,1)

        if month == 12:
            month_end_date = datetime(year+1,1,1)
        else:
            month_end_date = datetime(year, month+1, 1)

        month_records = Transaction.query.filter(Transaction.account_id==account.id,
                                                Transaction.timestamp >= month_start_date,
                                                Transaction.timestamp < month_end_date,
                                                Transaction.transaction_type == 'debit'
                                                ).all()
        invest_month_records = DematHoldings.query.filter(DematHoldings.user_investments==account.id,
                                                        DematHoldings.buy_date >= month_start_date,
                                                        DematHoldings.buy_date < month_end_date,
                                                        DematHoldings.invest_type == 'buy'
                                                        ).all()
        if not month_records and not invest_month_records:
            return jsonify({"message":"Records cannot found!"}),404
        monthly_records = []
        for mr in month_records:
            monthly_records.append({
                "entry_type":"transactions",
                "amount":mr.amount,
                "transaction_type":mr.transaction_type,
                "category":mr.category,
                "status":mr.status,
                "timestamp":mr.timestamp
            })
        for i in invest_month_records:
            monthly_records.append({
                "entry_type":"investments",
                "stock_name":i.stock_name,
                "amount":i.buy_price * i.quantity,
                "timestamp":i.buy_date,
                "quantity":i.quantity
            })
        tranx_sum = sum(d.amount for d in month_records if d.transaction_type == "debit")
        invest_sum = sum([i.buy_price* i.quantity for i in invest_month_records if i.invest_type == 'buy'])
        debit_total = tranx_sum + invest_sum
        

        #pie chart
        pie_chart_data = db.session.query(
            Transaction.category.label('category'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= month_start_date,
            Transaction.timestamp < month_end_date,
            Transaction.transaction_type == "debit"
        
        ).group_by(
            Transaction.category
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
        start_date = datetime.strptime(datee,'%Y-%m-%d')
        
        end_date = start_date + timedelta(days=1)
        lists = []
        view_records = Transaction.query.filter(Transaction.account_id == account.id,
                                                Transaction.timestamp >= start_date,
                                                Transaction.timestamp < end_date,
                                                Transaction.transaction_type == 'debit'
                                                ).all()
        view_investments = DematHoldings.query.filter(DematHoldings.user_investments == account.id,
                                                DematHoldings.buy_date >= start_date,
                                                DematHoldings.buy_date < end_date,
                                                DematHoldings.invest_type == 'buy'
                                                ).all()
        if not view_records and not view_investments:
            return jsonify({"message":"We could not found transaction history for that sepcific date please verify the date"}),404
        for record in view_records:
            lists.append({
                "entry_type":"transactions",
                "amount":record.amount,
                "transaction_type":record.transaction_type,
                "category":record.category,
                "status":record.status,
                "timestamp":record.timestamp
        })
        for i in view_investments:
            lists.append({
                "entry_type":"investments",
                "stock_name":i.stock_name,
                "amount":i.buy_price*i.quantity,
                "quantity":i.quantity,
                "timestamp":i.buy_date
            })
        debits = sum(d.amount for d in view_records if d.transaction_type == 'debit')
        invest_debits = sum([f.buy_price*f.quantity for f in view_investments if f.invest_type == 'buy'])

        debit_sum = debits + invest_debits

        
        return jsonify({"message":"Success","date_wise_records":lists,"debit_total":debit_sum}),200
    
    elif data.get('type') == 'year_wise':
        account = Account.query.filter_by(user_id=user.id).first()
        if not account:
            return jsonify({"message":"Unauthorized User"}), 401

        year = int(data.get('selectyear'))
        year_start_date = datetime(year, 1, 1)
        year_end_date = datetime(year + 1, 1, 1)

        find_transaction = Transaction.query.filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= year_start_date,
            Transaction.timestamp < year_end_date,
            Transaction.transaction_type == 'debit'
        ).order_by(Transaction.timestamp.asc()).all()

        find_investments = DematHoldings.query.filter(
                    DematHoldings.user_investments == account.id,
                    DematHoldings.buy_date >= year_start_date,
                    DematHoldings.buy_date < year_end_date,
                    DematHoldings.invest_type == 'buy'
                ).order_by(DematHoldings.buy_date.asc()).all()

        if not find_transaction and not find_investments:
            return jsonify({"message":"Transaction Not found!"}),404

        lists = []
        for t in find_transaction:
            lists.append({
                "entry_type":"transactions",
                "transaction_type":t.transaction_type,
                "amount": t.amount,
                "category": t.category,
                "date": t.timestamp,
                "status": t.status
                
            })
        for i in find_investments:
            lists.append({
                "entry_type":"investments",
                "stock_name":i.stock_name,
                "amount":i.buy_price*i.quantity,
                "timestamp":i.buy_date,
                "quantity":i.quantity
            })

        transx_sum = sum(d.amount for d in find_transaction if d.transaction_type == 'debit')
        invest_s = sum([d.buy_price *d.quantity for d in find_investments if d.invest_type == 'buy'])
        debit_sum  = transx_sum + invest_s

        

        year_line_chart = db.session.query(
            func.strftime('%m',Transaction.timestamp).label('month'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= year_start_date,
            Transaction.timestamp < year_end_date,
            Transaction.transaction_type == 'debit'
        ).group_by(
            func.strftime('%m',Transaction.timestamp)
        )
        
        yearly_data = []
        for y in year_line_chart:
            yearly_data.append({
                "month":y.month,
                "amount":y.total_amount
            })

        yearly_pie_data = db.session.query(
            Transaction.category.label('category'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.account_id == account.id,
            Transaction.timestamp >= year_start_date,
            Transaction.timestamp < year_end_date,
            Transaction.transaction_type == 'debit'
        ).group_by(
            Transaction.category
        )

        
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
                    .order_by(Transaction.timestamp.asc()).first()
                
    #investment years:
    investments_year = DematHoldings.query.filter_by(user_investments=account.id)\
                        .order_by(DematHoldings.buy_date.asc()).first()
    if not transaction_year and not investments_year:
        return jsonify({"message":"Record not found", "years":[]}),404

    transaction_start_year = transaction_year.timestamp.year if transaction_year else None  #2026[2026]
    investment_start_year = investments_year.buy_date.year if investments_year else None  #2026[2027]
    possible_years = [y for y in [transaction_start_year,investment_start_year] if y is not None]#[2027,2026]

    start_year = min(possible_years)
    current_year = datetime.utcnow().year


    years = list(range(start_year,current_year+1))
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
    
    
    stock = yf.Ticker(f"{stripe}.NS")

    data = stock.history(period="1d", interval="1m")
    if data.empty:
        return "Data not found",409
    lastest = data.tail(1)
    
    return {
        'price':float(lastest['Close'].values[0]),
        'volatality':round(lastest['High'].values[0] - lastest['Low'].values[0].min(),2)
    }


#used web socket to provide the live market updates to the users who are connected to the socket network and they can see the live market updates of the company they have selected.
active_stock = {}
@socketio.on('check_market_updates')
@jwt_required(locations=['cookies'])
def live_market_updates(data):
    stripe = data.get("stripe").upper().strip()
    if not stripe:
        return jsonify({"message":"Stripe is empty"}),401
    sid = request.sid 
    active_stock[sid] = stripe
    print(f"sid:{sid}, stripe:{stripe}, active_stock{active_stock}")
    
    

    while True:
        if active_stock.get(sid) != stripe:
            print(f"sid:{sid}, stripe:{stripe}, active_stock{active_stock}")
            break
        
        data = get_live_stock_data(stripe)

            
        socketio.emit('market_update',data,room=sid)
            
        socketio.sleep(5)
   
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
            new_stock_holding = DematHoldings(stock_name = data['company'],quantity=quantity,buy_price = totalPrice ,user_investments=account_have.id,invest_type='buy')
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
            avg_price = holds_or_not.buy_price / holds_or_not.quantity
            returns = (price - avg_price) * sell_quantity
            holds_or_not.buy_price -= avg_price * sell_quantity 
            holds_or_not.quantity -= sell_quantity
            account_have.balance += price * sell_quantity
            holds_or_not.invest_type = 'sell'
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
    active_stock.pop(request.sid , None)

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






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


