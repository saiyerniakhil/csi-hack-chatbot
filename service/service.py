import os
import json
import time
import requests
import random
from collections import OrderedDict
import urllib.request
from tqdm import tqdm
import langchain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma, FAISS
from langchain import OpenAI, VectorDBQA
from langchain.chat_models import AzureChatOpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.docstore.document import Document
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain




from IPython.display import Markdown, HTML, display  



def printmd(string):
    display(Markdown(string))    

BLOB_CONTAINER_NAME = "chatbottrainingdata"
BASE_CONTAINER_URL = "https://carpediemstoragebucket.blob.core.windows.net" + BLOB_CONTAINER_NAME + "/"

MODEL = "gpt-35-turbo-16k" # options: gpt-35-turbo, gpt-35-turbo-16k, gpt-4, gpt-4-32k

# def load_envs():
#     load_dotenv("env2.env")
    
    # env_name = ".env2.env" # change to use your own .env file

