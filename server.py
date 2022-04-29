from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
from tqdm import tqdm
import xml.dom.minidom
import zipfile  
import pdfplumber
import warnings
import spacy
import re

# import docx 
import json
import os  # standard library imports first
warnings.filterwarnings("ignore")
app= Flask(__name__)
# nlp = spacy.load("en_core_web_md")
updated_model_dir = '/home/softuvo/Garima/SpacyNER/updated_model'
# Use updated saved model
print("Loading updated model from:", updated_model_dir)
nlp = spacy.load(updated_model_dir)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Uploads')
CONVERTED_TO_TXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Converted_To_Txt')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_TO_TXT, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_TO_TXT'] = CONVERTED_TO_TXT

# ALLOWED_EXTENSIONS = {'pdf'} 
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/nertagging', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({"message": 'No file provided/Check the key, spelling or any space after or in the key.'})
            file = request.files['file']
            if file.filename == '':
                return jsonify({"message": 'No file selected.'})
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                return jsonify({"message": f'{file.filename} not allowed. Please send pdf and txt formats only.'})
            
            filename, file_extension =  os.path.splitext(file.filename)
            print(f'{filename}, {file_extension}')

            if (file_extension) == ".pdf":
                pages = {}
                text = pdfplumber.open(os.path.join(UPLOAD_FOLDER, file.filename))
                # print(text)
                # print("***********************************************************************************************************************")
                file_name = os.path.join(CONVERTED_TO_TXT, file.filename.replace('.pdf', '.txt'))
                if os.path.isfile(file_name):
                    os.remove(file_name)
                with open(file_name, 'w', encoding='utf-8') as txt_file:
                    for page in tqdm(text.pages):
                        pages[f'page {page.page_number}'] = page.extract_text()
                        txt_file.write(page.extract_text())
                        txt_file.write('\n')
                        txt_file.write('*' * 45)
                        txt_file.write('\n')
                
                val = []
                for idx, page in enumerate(pages):
                    val.append(pages[page])
                if val:
                    doc = nlp(str(val))
                    datum = {}
                    for idx, ent in enumerate(doc.ents):
                        if ent.label_ =="O" or ent.label_ == "DATE" or ent.label_ == "CARDINAL" or ent.label_ == "MONEY" or ent.label_ == "PRODUCT" or ent.text == "\n♦" or ent.text == "\n" or ent.text == "B-REVIEW'" or ent.text ==" B-TRAILER" or ent.label_== "WORK_OF_ART":
                            continue
                        datum[f'T{idx+1}'] =  {'text':ent.text, 'start':ent.start_char,'end': ent.end_char, 'label': ent.label_}    
                    return jsonify({"output":datum})
                else:
                    return jsonify({"message": "Data not uploaded properly"})
            
            elif file_extension == ".txt":
                file_name = os.path.join(CONVERTED_TO_TXT, file.filename)
                if os.path.isfile(filename):
                    os.remove(filename)
                with open((os.path.join(UPLOAD_FOLDER, file.filename)), "r") as text:
                    txt = text.read()
                    with open(file_name, "w") as output:
                        output.write(txt)
                       
                doc = nlp(str(txt))
                datum = {}
                for idx, ent in enumerate(doc.ents):
                    if ent.label_ =="O" or ent.label_ == "DATE" or ent.label_ == "CARDINAL" or ent.label_ == "MONEY" or ent.label_ == "PRODUCT" or ent.text == "\n♦" or ent.text == "\n" or ent.text == "B-REVIEW'" or ent.text ==" B-TRAILER" or ent.label_== "WORK_OF_ART":
                        continue
                    datum[f'T{idx+1}'] =  {'text':ent.text, 'start':ent.start_char,'end': ent.end_char, 'label': ent.label_}    
                return jsonify({"output":datum})

        else:
            return jsonify({"message": "Method not allowed"})
        
    except Exception as ex:
        print(ex)
        return jsonify({"message": "Allowed Entensions are .pdf and .txt"})
                    
if __name__ == '__main__':
	app.run(port=5001, debug=True)