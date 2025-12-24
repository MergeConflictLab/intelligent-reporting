from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import Flask, render_template
from playwright.sync_api import sync_playwright
import json
import os 
import random
import string
import base64
from EmailSender import EmailSender
from intelligent_reporting.profiling.DataSampler import DataSampler
from intelligent_reporting.profiling.DataSummarizer import DataSummarizer
from intelligent_reporting.profiling.DataVisualizer import DataVisualizer
from intelligent_reporting.profiling.DataCorrelater import DataCorrelater
from datetime import datetime
from intelligent_reporting.pipeline import Pipeline


app = Flask(__name__)
CORS(app)

USERS_FILE = "users.json"

@app.get("/")
def test():
    return "<h1>Hello! Flask is running.</h1>" 
def checkUser(email, users_data):
    for user_data in users_data["users"]:
        if(user_data["email"].lower()==email):
            return False
    return True 
def saveUsers(users_data):   
    with open("users.json", "w") as f:
       json.dump(users_data, f, indent=4)
def generate_key(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))                
@app.post("/signup")
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    users_data = None
    if not os.path.exists("users.json") or os.path.getsize("users.json") == 0:
        users_data = {"users": []}
        if not os.path.exists("users.json"):
            with open("users.json", "w") as f:
                 json.dump(users_data, f)
    else:
        with open("users.json", "r") as f:
            try:
                users_data = json.load(f)
            except json.JSONDecodeError:
                users_data = {"users": []}           
    if(checkUser(email.lower(), users_data)==False):
       return jsonify({"message": "Email already exists"}), 409
    #Add user  
    users_data["users"].append({
        "email": email,
        "password": password,
        "key": "",
        "date": "" 
    }) 
    saveUsers(users_data)
    return jsonify({"message": "Signup received", "data": data}), 200
def checkUserAndPassword(email, password):
    if not os.path.exists("users.json") or os.path.getsize("users.json") == 0:
        users_data = {"users": []}
        if not os.path.exists("users.json"):
            with open("users.json", "w") as f:
                 json.dump(users_data, f)
    else:
        with open("users.json", "r") as f:
            try:
                users_data = json.load(f)
            except json.JSONDecodeError:
                users_data = {"users": []} 
    for user_data in users_data["users"]:
        if(email==user_data["email"].lower() and
           password==user_data["password"]):
            user_data["key"] = generate_key()
            user_data["date"] = str(datetime.now())
            saveUsers(users_data)
            return [user_data["key"], user_data["date"]]
    return None    
@app.post("/signin")
def signin():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    value = checkUserAndPassword(email.lower(), password)
    if(value!=None):
       return jsonify({"message": "Signin successfull", "data": {"key": value[0], "date": value[1] }}), 200 
    return jsonify({"message": "Email or password incorrect"}), 401

save_base = "data"
def cleanOutputPath(path="data"):
    if not os.path.exists(path):
        return
    for item_name in os.listdir(path):
        item_path = os.path.join(path, item_name)
        if os.path.isfile(item_path):
            try:
                os.remove(item_path) 
                print(f"Deleted file: {item_name}")
            except Exception as e:
                print(f"Error deleting {item_name}: {e}")

@app.post('/retreiveImages')
def images_api():
    images_dir = 'results/figures'
    images = []
    for filename in os.listdir(images_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            with open(os.path.join(images_dir, filename), 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            images.append({
                "name": filename,
                "src": f"data:image/png;base64,{encoded}"
            })    
    print("Images has been sent")      
    return jsonify(images)

STILL_PROCESSING = False
@app.post("/uploadfiles")
def upload_files():
    global STILL_PROCESSING
    if(STILL_PROCESSING):
       return
    STILL_PROCESSING = True
    if 'myFile' not in request.files:
        return 'No file part', 400
    cleanOutputPath()    
    file = request.files['myFile']
    param_string = request.form.get('parametre')
    param_string = json.loads(param_string)
    os.makedirs(save_base, exist_ok=True)
    filepath = os.path.join(save_base, file.filename.split("/")[-1])
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    #'''
    extension = filepath.split(".")[-1]
    pipeline = Pipeline(file=f"./data/{file.filename}")
    data=None
    try:
        if(extension=="csv"):
            has_header = param_string["has_header"].rstrip()
            seperator = param_string["seperator"].rstrip()
            encoding = param_string["encoding"].rstrip()
            if(has_header!="" and seperator!="" and encoding!=""):
               data = pipeline.load(has_header=(has_header=="true"), seperator=seperator, encoding=encoding)
            else:
               data = pipeline.load()    
        elif(extension in ["xls", "xlsx"]):
            sheet_id = param_string["sheet_id"].strip()
            sheet_name = param_string["sheet_name"].strip()
            table_name = param_string["table_name"].strip()
            has_header = param_string["has_header"].strip()
            if(sheet_id!="" and sheet_name!="" and table_name!="" and has_header!=""):
                data = pipeline.load(sheet_id=int(sheet_id), sheet_name=sheet_name, table_name=table_name, has_header=(has_header=="true"))
            else:
                data = pipeline.load()    
        else:
            data = pipeline.load()

        typed, schema = pipeline.infer(data=data) 

        downcasted = pipeline.downcast(data=typed)

        RESULTS_DIR = "results"
        FIGURES_DIR = "figures"
        MAX_ROWS = 5  
        cleanOutputPath(path=f"{RESULTS_DIR}/{FIGURES_DIR}")
        sampler = DataSampler(df=downcasted, max_rows=MAX_ROWS, sample_dir = RESULTS_DIR)
        summarizer = DataSummarizer(df=downcasted, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR)
        visualizer = DataVisualizer(df=downcasted, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR, top_k_categories=5)
        correlater = DataCorrelater(df=downcasted)
 
        sample = sampler.run_sample()
        summary = summarizer.summary()
        visualizer.run_viz()
        correlater.run()
    except:
        return jsonify({"message": "Something went wrong"}), 409

    STILL_PROCESSING = False
    #'''   
    return jsonify({"message": "Data uploaded successfully"}), 200

@app.post("/sendPdfViaEmail")
def sendPdfViaEmail():
    data = request.get_json()
    email = data.get("email").strip()
    pageLink = data.get("pageLink")
    print(email, pageLink)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(
            pageLink,
            wait_until="networkidle"
        )

        pdf = page.pdf(
            format="A4",
            print_background=True
        )
        outputPath = "pdf"
        os.makedirs(outputPath, exist_ok=True)

        filepath = os.path.join(outputPath, "report.pdf")

        with open(filepath, "wb") as f:
            f.write(pdf)
        browser.close()

        emailSender = EmailSender()
        emailSender.send_email(receiver_email=email, 
                               subject="Intelligent Report", 
                               body="", folder_path="pdf")
    return jsonify({"message": "Email sended successfully!"}), 200
if __name__ == "__main__":
    app.run(debug=True)    