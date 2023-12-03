from flask import Flask, request
from flask_cors import CORS, cross_origin
import os
import json

from service import service, pdf_parser, search_helpers

def create_app():
    app = Flask(__name__)
    #loading env variables
    app.config.from_file("env.json", load=json.load)
    CORS(app)
    print(app.config)
    #initialize everything
    service.load_envs()
    # print(os.environ)
    #process pdfs and all 
    # load data from data/profile
    # parse pdfs by splitting them into pages and extracting text from them
    # upload chunks to Azure AI Search index (which has semantic search included)
    pdf_parser.process_pdf()
    # get search results
    search_helpers.get_search_results()
    
    

    return app

app = create_app()


@app.get("/")
def index():
    return {"message":"hello"}



@app.post("/chatservice")
@cross_origin()
def chatservice():
    data = request.get_json()
    print(data)
    return {"message":"hello"}