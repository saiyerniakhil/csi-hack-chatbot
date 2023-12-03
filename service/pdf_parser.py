from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import html
import base64
import os
import time
from openai import AzureOpenAI
from tqdm import tqdm
import json
import requests
from collections import OrderedDict



BLOB_CONTAINER_NAME = "chatbottrainingdata"
BASE_CONTAINER_URL = "https://carpediemstoragebucket.blob.core.windows.net" + BLOB_CONTAINER_NAME + "/"

### Create Azure Search Vector-based Index
def get_vector_profile_indices():
    profile_index_name = "carpediemsearchindex"
    vector_indexes = [profile_index_name]
    return vector_indexes


def parse_pdf(file, form_recognizer=False, formrecognizer_endpoint=None, formrecognizerkey=None, model="prebuilt-document", from_url=False, verbose=False):
    """Parses PDFs using PyPDF or Azure Document Intelligence SDK (former Azure Form Recognizer)"""
    offset = 0
    page_map = []
    if not form_recognizer:
        if verbose: print(f"Extracting text using PyPDF")
        reader = PdfReader(file)
        pages = reader.pages
        for page_num, p in enumerate(pages):
            page_text = p.extract_text()
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)
    else:
        if verbose: print(f"Extracting text using Azure Document Intelligence")
        credential = AzureKeyCredential(os.getenv("FORM_RECOGNIZER_KEY"))
        form_recognizer_client = DocumentAnalysisClient(endpoint=os.getenv("FORM_RECOGNIZER_ENDPOINT"), credential=credential)
        
        if not from_url:
            with open(file, "rb") as filename:
                poller = form_recognizer_client.begin_analyze_document(model, document = filename)
        else:
            poller = form_recognizer_client.begin_analyze_document_from_url(model, document_url = file)
            
        form_recognizer_results = poller.result()

        for page_num, page in enumerate(form_recognizer_results.pages):
            tables_on_page = [table for table in form_recognizer_results.tables if table.bounding_regions[0].page_number == page_num + 1]

            # mark all positions of the table spans in the page
            page_offset = page.spans[0].offset
            page_length = page.spans[0].length
            table_chars = [-1]*page_length
            for table_id, table in enumerate(tables_on_page):
                for span in table.spans:
                    # replace all table spans with "table_id" in table_chars array
                    for i in range(span.length):
                        idx = span.offset - page_offset + i
                        if idx >=0 and idx < page_length:
                            table_chars[idx] = table_id

            # build page text by replacing charcters in table spans with table html
            page_text = ""
            added_tables = set()
            for idx, table_id in enumerate(table_chars):
                if table_id == -1:
                    page_text += form_recognizer_results.content[page_offset + idx]
                elif not table_id in added_tables:
                    page_text += table_to_html(tables_on_page[table_id])
                    added_tables.add(table_id)

            page_text += " "
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)

    return page_map

#function to create from pdf to html
def table_to_html(table):
    table_html = "<table>"
    rows = [sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index) for i in range(table.row_count)]
    for row_cells in rows:
        table_html += "<tr>"
        for cell in row_cells:
            tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
            cell_spans = ""
            if cell.column_span > 1: cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span > 1: cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html +="</tr>"
    table_html += "</table>"
    return table_html

#text to base64 encoding helper function
def text_to_base64(text):
    # Convert text to bytes using UTF-8 encoding
    bytes_data = text.encode('utf-8')

    # Perform Base64 encoding
    base64_encoded = base64.b64encode(bytes_data)

    # Convert the result back to a UTF-8 string representation
    base64_text = base64_encoded.decode('utf-8')

    return base64_text

def get_client():
    client = AzureOpenAI(
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#rest-api-versioning
        api_version="2023-07-01-preview",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        # https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    return client



def getmebedding(text):
    client = get_client()
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return list(list(dict(response)['data'][0]))[0][1]

def process_pdf():
    directory = 'data/profiles'
    filepdfs= []

    # Setup the Payloads header
    headers = {'Content-Type': 'application/json','api-key': os.getenv('AZURE_SEARCH_KEY')}
    params = {'api-version': os.getenv('AZURE_SEARCH_API_VERSION')}
    
    # iterate over files in
    # that directory
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        # checking if it is a file
        if os.path.isfile(f):
            #print(f)
            filepdfs.append(f)
    
    pdf_pages_map = dict()

    for pdf in filepdfs:
        print("Extracting Text from",pdf,"...")
        
        if not '.amlignore' in pdf:

            # Capture the start time
            start_time = time.time()
            
            # Parse the PDF
            pdf_path = pdf
            pdf_map = parse_pdf(file=pdf_path, form_recognizer=True, verbose=True)
            pdf_pages_map[pdf]= pdf_map
            
            # Capture the end time and Calculate the elapsed time
            end_time = time.time()
            elapsed_time = end_time - start_time

            print(f"Parsing took: {elapsed_time:.6f} seconds")
            print(f"{pdf} contained {len(pdf_map)} pages\n")
    
    print(f"Total contained {len(pdf_pages_map)} pages\n")

    for pdfname,pdfmap in pdf_pages_map.items():
        print("Uploading chunks from",pdfname)
        for page in tqdm(pdfmap):
            try:
                page_num = page[0] + 1
                content = page[2]
                head_tail = os.path.split(pdfname)
                book_url = BASE_CONTAINER_URL + head_tail[1]
                print("book_url", book_url)
                upload_payload = {
                    "value": [
                        {
                            "id": text_to_base64(pdfname + str(page_num)),
                            "title": f"{pdfname}_page_{str(page_num)}",
                            "chunk": content,
                            "chunkVector": getmebedding(content if content!="" else "-------"),
                            "name": pdfname,
                            "location": book_url,
                            "page_num": page_num,
                            "@search.action": "upload"
                        },
                    ]
                }

                r = requests.post(os.getenv('AZURE_SEARCH_ENDPOINT') + "/indexes/" + get_vector_profile_indices() + "/docs/index",
                                    data=json.dumps(upload_payload), headers=headers, params=params)
                if r.status_code != 200:
                    print(r.status_code)
            except Exception as e:
                print("Exception:",e)
                continue

    return pdf_pages_map
