from flask import Flask, request
from flask_cors import CORS, cross_origin
import os
import json
from dotenv import load_dotenv
from nbconvert import HTMLExporter

from service import service, pdf_parser, search_helpers, azure_helpers

def create_app():
    app = Flask(__name__)
    #loading env variables
    load_dotenv(".env2.env") 
    # app.config.from_file("env.json", load=json.load)
    CORS(app)
    
    #process pdfs and all 
    # load data from data/profile
    # parse pdfs by splitting them into pages and extracting text from them
    # upload chunks to Azure AI Search index (which has semantic search included)
    pdf_parser.process_pdf()
    
    
    

    return app

app = create_app()


@app.get("/")
def index():
    return {"message":"hello"}



@app.post("/chatservice")
@cross_origin()
def chatservice():
    data = request.get_json()
    # get search results
    question = data["question"]
    result = search_helpers.get_answer(question)
    
   

    return {"response": result}