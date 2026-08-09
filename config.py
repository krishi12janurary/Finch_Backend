#installing python-dotenv to load the value which are there in environment file.
import os
from dotenv import load_dotenv# now.ev is not an module or valid python file which can be stored easily that's why we stored those secret_keys into the aptop environemnt now to get read that we need something so for which we have tool dotenv through it's load_dotnev() function it will read the environemnt file and our key's value and we can use that further.

load_dotenv()

Bank_API_key = os.environ.get("Bank_API_key")
Bank_Base_URL = os.environ.get("Bank_Port")
#so the question can arise that than why we cannot easily write those secret or app_key into an simple python file s the answer is when we put this project into github we live this project if simply written secrets key into .py file that would expose into github which is not what we want so we create that env file which will permantly live in our computer like anyother file 
#but what will happen that when load_dotnev will call that file that file content will save into an temporary varaible now once you vanish the terminal or close it that variable and it's content will earse so everytime you call a new variable same content so yaa.

# print(Bank_API_key)
# print(Bank_Base_URL)
