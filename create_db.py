from app import app
from extensions import db
from models import Account,User,UserAdditionalInfo,DematHoldings,DematAccount
from sqlalchemy import inspect



with app.app_context():
    user = User.query.filter_by(email='krishitrialemail@gmail.com').first()
    if user:
        acc = Account.query.filter_by(user_id=user.id).first()
        if acc:
            demat_holding = DematHoldings.query.filter_by(user_investments=acc.id).first()
            if demat_holding:
                demat_holding.invest_type = 'buy'
                db.session.commit()
                print("Added successfully")
            else:
                print("Not found")
        else:
            print("not found")
    else:
        print('User not found!')


        
        
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