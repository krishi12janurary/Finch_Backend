import re
import os
import cv2
import zxingcpp
import requests
from datetime import datetime,date
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
from deepface import DeepFace


OCR_API_KEY = "K88691552088957"

def read_text_from_img(img_path):
   
    with open(img_path, "rb") as f:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": f},
            data={
                "apikey":            OCR_API_KEY,
                "language":          "eng",
                "isOverlayRequired": False,
                "detectOrientation": True,
                "scale":             True,
                "OCREngine":         2
            }
        )
        result = response.json()
        print("[OCR Raw Response]", result)  # add this to debug
        if result.get("IsErroredOnProcessing"):
            return False, f"OCR API error: {result.get('ErrorMessage', 'Unknown')}"
        parsed = result.get("ParsedResults")
        if not parsed:
            return False, "No text found in image"
        return True, parsed[0]["ParsedText"].strip()


def identify_pan_text(pan_num):
    match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]",pan_num.upper())
    return match.group() if match else None



def dob_matches(text,dob):#take two values text in which OCR dob is mentioned and dob where user entered dob is mentioned it's not value it's parameters name we are keeping the actuall values we will put as an arguments in our main function.

    date_convert = datetime.strptime(dob,"%Y-%m-%d").date()#will handover you the pure date instead the whole datetime like date : hour.second we don't want that so that's why we write from these only takes date.
    today_year = date.today()
    age = today_year.year - date_convert.year - ((today_year.month, today_year.day) < (date_convert.month, date_convert.day))# now here when today is less than user's birthday month that's says the user has not yet celebrated their birthday and the age is 17 now if we erase that part that despite of being 17 the user has been counted as 18 which is not accurate while as it's tuple they start verifying the condition from left so hre the month is 5 and 12 nowe 5 is less than 12 now if someone's birthdate is on may and currently also it's may than there tuple will not decide from first condition than it will check from second condition day that's why date and month is integral to write now it's less python uses 1 to subtract and if it's greater than python uses 0 so 18 -1 =17 and vice-versa.

    if age < 18:
        return False, "You are not eligible for account opening due to age restriction!"
        
    date_formats = [
    date_convert.strftime("%d/%m/%Y"),
    date_convert.strftime("%d-%m-%Y"),
    date_convert.strftime("%Y-%m-%d"),
    date_convert.strftime("%d/%m/%y")
    ]#  date_convert.strftime("%d/%m/%y") writing this the actual dates are being stored in this formats in that list.

    if any(date_there in text for date_there in date_formats):
        return True, "Date of Birth matches!"
    
    return False,"Date of birth does not match!"
    
    #here by writing date_there in text we are directly checking the stored user date with ocr detected date with format.

def name_matches(text,name):
    
    return name.strip().lower() in text.strip().lower()

def check_adhar_qr(adhar_path):
    img = cv2.imread(adhar_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False,"Could not Open image"
    results = zxingcpp.read_barcodes(img)
    if not results:
        return False,"No QR code found in the image"
    for result in results:
        print(f"QR Code Text: {result.text}")
        return True, result.text
    return False,"QR code is not readable"
def check_pan_qr(pan_path):
    img = cv2.imread(pan_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False,"Could not Open image"
    results = zxingcpp.read_barcodes(img)
    if not results:
        return False,"No QR code found in the image"
    for result in results:
        print(f"QR Code Text: {result.text}")
        return True, result.text
    return False,"QR code is not readable"


def verify_phone_num(text,phone_num):
    phone_pattern = re.search(r"\b\d{10}\b",text)
    if not phone_pattern:
        return False, "Phone number not found in the image"
    if phone_pattern.group() != phone_num:
        return False, "Phone number does not match with the one on the Adhar card"
    
    
    
    return True, "Phone number matches with the one on the Adhar card"



def adhar_card_name_match(adhar_path,name,phone_num):
    qr_status,qr_result = check_adhar_qr(adhar_path)

    if not qr_status:
        print(f"QR Code Error: {qr_result}")
        # return False, qr_result
        
    txt_status,txt_msg = read_text_from_img(adhar_path)
    if not txt_status:
        return False, txt_msg
    print(f"OCR Text: {txt_msg}")
    adhar_required_data = [
        "unique identification authority of india",
        "government of india",
        "uidai",
        "आधार"
    ]
    text_lower = txt_msg.lower()
    if not any(keyword in text_lower for keyword in adhar_required_data):
        return False, "The uploaded document does not appear to be an Aadhaar card."
    adhar_num_pattern = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", txt_msg)#4 digit space optional like that so on someone with 1234-4567-896 would fail here after every 4 digit there can be space or no space./b means we can understand it like only that adhar card number would be get if that sticked to another word than it will not determine so even if the user write andadharnum than it will not recommand it at all without /b if the adhar-card is weritten like krishiadharnum than even its invalid it will get counted but /b at the start and /b at the end means only the adhar num would be get counted and if its sticked to any other word than it will not get counted at all.

    if not adhar_num_pattern:
        return False, "Aadhaar number not found in the image"
    

    if not name_matches(txt_msg,name):
        return False,"Name does not match with the one on the Adhar card"
    
    
    
    
    phone_status,phone_msg = verify_phone_num(txt_msg,phone_num)
    if not phone_status:
        return False, phone_msg
    

    


    
    
    return True,"Adhar Verified Successfully!"

def pan_card_verifying(dob,pan_path):
    qr_code_status,qr_code_msg = check_pan_qr(pan_path)

    if not qr_code_status:
        print(f"QR Code Error: {qr_code_msg}")
        # return False,"QR not detected!"
    
    txt_status,txt_msg = read_text_from_img(pan_path)
    if not txt_status:
        return False,txt_msg
    print("OCR PAN TEXT:",txt_msg)
    pan_essentials = [
        "INCOME TAX DEPARTMENT",
        "GOVT. OF INDIA",
        "Permanent Account Number Card"
    ]
    txt_upper = txt_msg.upper()
    if not any(keyword in txt_upper for keyword in pan_essentials):
        return False,"No an valid pan card"
    
    pan_status= identify_pan_text(txt_msg)
    if not pan_status:
        return False,"PAN NUMBER is invalid!"
    
    dob_status, dob_msg = dob_matches(txt_msg,dob)
    if not dob_status:
        return False, dob_msg
    
    return True,"Pan verified!"



def verifying_face_identity(face_path):
    try:
        result  = DeepFace.verify(
            img1_path=  face_path,#instead of pan path we are here writing face_path so it easily get work later we can do pan_path
            img2_path=  face_path,
            model_name="Facenet512",
            detector_backend="retinaface",
            enforce_detection=True
        )

        if not result['verified']:
            return False, "Face did not match with the uploaded selfie"
        
        if result['distance'] < 0.45:
            return True,"Face identification success"
        

        

        

        return False, "Face did not match with the uploaded selfie"
    
    except Exception as e:
        return False, f"Face verification failed: {str(e)}"


#main function:
def verifying_ocr(name,dob,phone_num,pan_path,adhar_path,face_path):

    adhar_status,adhar_msg = adhar_card_name_match(adhar_path,name,phone_num)
    if not adhar_status:
        return False, adhar_msg
    
    
    
    pan_status,pan_msg = pan_card_verifying(dob,pan_path)
    if not pan_status:
        return False, pan_msg
    
    
    face_status,face_msg = verifying_face_identity(face_path)
    if not face_status:
        
        return False, face_msg
    

    return True,"KYC is being verifying, please wait.."


    



