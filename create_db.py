from app import app
from extensions import db
from models import Account,User,UserAdditionalInfo,DematHoldings,DematAccount,KYC_Model,Transaction
from sqlalchemy import inspect
import secrets



with app.app_context():

    
    db.drop_all()
    db.create_all()

print("Database created successfully.")

    