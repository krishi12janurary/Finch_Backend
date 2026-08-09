import requests
from config import Bank_Base_URL,Bank_API_key


token = None
def app_login():
    global token
    response = requests.post(f'{Bank_Base_URL}/first_verify_the_identity/bank_app',
                            headers={"Authorization":f"Bearer {Bank_API_key}"},
                            )
    data = response.json()
    token = data.get('token')
    return data


def submitting_kyc_form(kyc_form):
    global token
    print(token)
    response = requests.post(f'{Bank_Base_URL}/bank/kyc_submission_data',
                            json=kyc_form,
                            headers={"Authorization":f"Bearer {token}"},
                            
                            )
    return response.json()

def collecting_user_status(kyc_id):
    global token
    print(token)
    response = requests.post(f'{Bank_Base_URL}/bank/approving_the_user_kyc/{kyc_id}',
                            headers={"Authorization":f"Bearer {token}"})
    return response.json()

def bank_add_balance(bank_id,balance_amt,wallet_ref):
    global token
    lists  = []
    lists.append({
    "bank_id":bank_id,
    "balance_amt":balance_amt,
    "user_wallet_ref":wallet_ref
    })
    response = requests.post(f'{Bank_Base_URL}/bank/add_balance_approval_route',
                            json = lists,
                            headers={"Authorization":f"Bearer {token}"})
    return response.json()

def updation_bal_route(**kwargs):
    global token
    lists = []

    lists.append({
        "sender_acc":kwargs.get("sender_acc"),
        "reciever_acc": kwargs.get('reciever_acc'),
        "amount":kwargs.get('amount'),
        "wallet_ref": kwargs.get('wallet_ref')

    })
    response = requests.post(f'{Bank_Base_URL}/bank/balance_updation_route',
                            json=lists,
                            headers={"Authorization":f"Bearer {token}"})
    return response.json()

def demat_acc_approval(bank_id):
    global token
    response = requests.post(f'{Bank_Base_URL}/bank/demat_acc_opening_approval/{bank_id}',
                            headers={"Authorization":f"Bearer {token}"})
    return response.json()

