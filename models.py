from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # user_wallet = db.Column(db.Float, nullable=False, default=1000.00)
    role = db.Column(db.String, nullable=False, default="user")
    verify_status = db.Column(db.Boolean, nullable=False, default=False)
    verify_token = db.Column(db.String(150), nullable=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.Float, nullable=True)
    otp_status = db.Column(db.Boolean,nullable=False,default=False)
    kyc = db.relationship('KYC_Model', backref=db.backref('kyc', lazy=True))
    last_updated = db.Column(db.DateTime,nullable=True,default=datetime.utcnow)
    inactive_count = db.Column(db.Integer,nullable=False,default=0)

    

    def set_password(self,password):
        self.password = generate_password_hash(password)#generate password hash takes the password entered by the user convert it inot an immutable hash 
        
    def check_password(self,password):
        return check_password_hash(self.password,password)#while checkpassword hash when user visit the app again it checks the password again with his generated passwords hash if it matches then it return true else false(error).
    
    def set_app_password(self,app_password):
        self.app_password = generate_password_hash(app_password)
        
    def check_app_password(self,app_password):
        return check_password_hash(self.app_password,app_password)
    

    def __repr__(self):#this is just to represent or print the user name and email when we query the database for user-1 details it will print the username and email instead of whole details.
        return f"User('{self.username}', '{self.email}')"#when user-1 enter their details than through self the user-one details only get dispalyed .
    
#self- let's say an user-1 is creating an aaccount and he has entered his name , email and password now through self we are telling attach that password to user-1 identity now user-2 entered his details than the password will attach to his identity and so on.
#self in simple terms is a reference to that user-identity or anything.
#taking an human example signing an property which consists our own name that belongs to us that's how self sticks the identity to an particular thing.
#return check_password_hash(self.password,password) which here in the self.password is an hashed generated password and password is an plain text:
#so what happens let's say user-1 login to the app enter the detail the app check the user is there or not if user is there than the user entered password get converted into hash check with saved hashes through self.password if it matches it retrive whole user-1 detail else throw an error.
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_num = db.Column(db.String(20) , unique=True, nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)#createsan actual column in the account table which is linked to user table
    account_type = db.Column(db.String(50), nullable=False, default="Saving")
    bank_dec_id = db.Column(db.Integer, unique=True,nullable=False)
    user = db.relationship('User', backref=db.backref('accounts', lazy=True))#this is to create a relationship between user and account table through user_id foreign key and backref is to create a reverse relationship from account to user and lazy true means it will load the related data only when we access it not at the time of querying the database for user details.
    acc_status = db.Column(db.String(20), nullable=False, default="inactive")
    app_password = db.Column(db.String(255), nullable=False,default="")
    demat_holding = db.relationship('DematAccount',backref=db.backref('account',lazy=True))#ohhh yahhh i mean we will add relationships to accounts becuase we can already query which account-id has demat holding but if i want to ask that back from account side than relationship has to be stick there where we can query like from account that how much demat_holding this account_id has correct with backref = created name account
    account_ifsc = db.Column(db.String(120),nullable=False)



    def set_password(self, app_password):
        self.app_password = generate_password_hash(app_password)

    def check_password(self, app_password):
        return check_password_hash(self.app_password, app_password)
    
class DematHoldings(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    stock_name = db.Column(db.String(40), nullable=False)
    quantity = db.Column(db.Integer,nullable=False,default=0)
    buy_price = db.Column(db.Float, nullable=False,default=0.0)
    buy_date = db.Column(db.DateTime,default=datetime.utcnow)
    user_investments = db.Column(db.Integer,db.ForeignKey('account.id'))
    invesments = db.relationship('Account',backref=db.backref('invest_user',lazy=True))
    

class DematAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    acc_have = db.relationship('Account',backref=db.backref('user_demat',lazy=True))
    bank_approval = db.Column(db.String(100),nullable=False,default='pending')
    dem_account_id = db.Column(db.Integer,nullable=False)

class UserAdditionalInfo(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    income = db.Column(db.Float, nullable=False,default=0.0)
    address = db.Column(db.String(500),nullable=False,unique=True)
    city = db.Column(db.String(150), nullable=False)
    state = db.Column(db.String(150),nullable=False)
    nominee = db.Column(db.String(300),nullable=False)
    occupation = db.Column(db.String(400),nullable=False)
    earning_members = db.Column(db.Integer,nullable=False)
    total_family_members = db.Column(db.Integer,nullable=False)
    relation_occupation = db.Column(db.Integer,nullable=True)
    relation_income = db.Column(db.Float,nullable=True)
    pincode = db.Column(db.Integer,nullable=False)
    age = db.Column(db.Integer,nullable=False)
    gender = db.Column(db.String(200),nullable=False)
    family_type = db.Column(db.String(300),nullable=False)
    blood_relation = db.Column(db.String(100),nullable=True)
    maritial_status = db.Column(db.String(50),nullable=True)
    children = db.Column(db.Integer,nullable=True)
    users_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)


class KYC_Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(15), nullable=False)
    country_code = db.Column(db.String(5), nullable=False)
    date_of_birth = db.Column(db.String(50), nullable=False)
    kyc_status = db.Column(db.String(30), nullable=False, default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    pan_img_path = db.Column(db.String(255), nullable=False)
    adhar_img_path = db.Column(db.String(255), nullable=False)
    user_kyc = db.relationship('User', backref=db.backref('kyc_model', lazy=True))
    ocr_status = db.Column(db.Boolean, nullable=False,default=False)
    bank_approved = db.Column(db.Boolean, nullable=False,default=False)

    
    
    



    


    

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(30), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', backref=db.backref('transactions', lazy=True))#this is to create a relationship between account and transaction table through account_id foreign key and backref is to create a reverse relationship from transaction to account and lazy true means it will load the related data only when we access it not at the time of querying the database for account details.
    status = db.Column(db.String(30),nullable=False,default="pending")
    timestamp = db.Column(db.DateTime, nullable=False,default=datetime.utcnow)#when we write utcnow() with brackets it means when we run or start the app it set the default time as it and when the transaction performed at 3:45 than also the transaction recrds set the timstamp is 3:40 as it gets freeze for every transaction, while without() it sets time when the app starts but changes when transaction are being performed.
    sender_acc = db.Column(db.String(15),nullable= False)
    recevier_acc = db.Column(db.String(15),nullable= False)
    category = db.Column(db.String(100),nullable=False,default="Food/Beverages")
    # wallet_ref = db.Column(db.String(100),nullable=False,unique=True)
    
    # langitude = db.Column(db.Float,nullable=True)#whereas it about negative number-90 means the person is transferring money from south side ansd vice-versa
    # longitude = db.Column(db.Float,nullable=True)#measure how far you are from earth east or west as earth is on 0 longitude and if it's say -180 that means you are talking from west side while if it ranges in positive number it means you are from east side position



# class Investments(db.Model):
#     id = db.Column(db.Integer, primary_key=True)#creating an id column
#     investment_type = db.Column(db.String(40), nullable=False)#create an column which will describe type of investments like stocks, ETFs, mutual funds etc.
#     amount = db.Column(db.Float, nullable=False)#create an column which will consists of amount of which investments you made.
#     user_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)#creates an column which describe which account has made an investments than through account we can identify which user had made an investments.
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow())#this is to keep track of when the investments was made and it will automatically set the current time when the investments was made.
#     investments = db.relationship('Account', backref = db.backref('investments',lazy=True))#this line refers to the relationship between account that means if we want to find which account-id has done which investments we cnan just query account-1 and we will able to find-out the investments of that account-id.





#accchan okay whole investments table and account table in under this and if we query something than through fething the account number than query find the investment type from the account-1 so that relationship is created trough this.