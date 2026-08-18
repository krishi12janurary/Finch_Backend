from app import app
from extensions import db
from models import Account,User,UserAdditionalInfo,DematHoldings,DematAccount,KYC_Model,Transaction
from sqlalchemy import inspect
import secrets



with app.app_context():

    user = User.query.filter_by(email="jagrutigandhi139@gmail.com").first()
        
    if user:
        acc = Account.query.filter_by(user_id=user.id).first()
        if acc:
            password = "jagu@403"
            acc.set_password(password)
            db.session.commit()
        else:
            print("Not found")
    else:
        print("not found!")
            
        

        
    #     db.session.delete(user)
    #     db.session.commit()
    #     print("Deleted successfully!")
    # else:
    #     print("not found")

        

        # if kyc_details:
        #     # db.session.delete(kyc_details)
        #     # db.session.commit()
        #     print("deleted successfully!",kyc_details.occupation)

        # 4. KYC
        # banks_details = KYC_Model.query.filter_by(user_id=3).first()
        # if banks_details:
        #     print(banks_details.kyc_status)
        # else:
        #     print("Not Found")

            
       

        
        
    # else:
    #     print("user not found!")
    # inspector = inspect(db.engine)
    # columns = inspector.get_columns('account')
    # for col in columns:
    #     print(col['name'], col['type'])
    
    # acc = Account.query.filter_by(id=3).first()
    # acc.set_password("BdF4OzKg")
    # db.session.commit()

    
#     db.drop_all()
#     db.create_all()

# print("Database created successfully.")

    