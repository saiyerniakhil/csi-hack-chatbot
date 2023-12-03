import os
from collections import OrderedDict
import requests
import json
from langchain.chat_models import AzureChatOpenAI
from langchain.docstore.document import Document
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from service.pdf_parser import getmebedding
from service.azure_helpers import get_prompt_template, get_vector_profile_indices, model_tokens_limit, num_tokens_from_docs, num_tokens_from_string



MODEL = "gpt-35-turbo-16k" # options: gpt-35-turbo, gpt-35-turbo-16k, gpt-4, gpt-4-32k
COMPLETION_TOKENS = 1000


#This is what is called upon request hit
def get_search_results(query: str, indexes: list, 
                       k: int = 5,
                       reranker_threshold: int = 1,
                       sas_token: str = "",
                       vector_search: bool = False,
                       similarity_k: int = 3, 
                       query_vector: list = []):
    
    headers = {'Content-Type': 'application/json','api-key': os.environ["AZURE_SEARCH_KEY"]}
    params = {'api-version': os.environ['AZURE_SEARCH_API_VERSION']}

    agg_search_results = dict()
    
    for index in indexes:
        search_payload = {
            "search": query,
            "queryType": "semantic",
            "semanticConfiguration": "default",
            "count": "true",
            "speller": "lexicon",
            "queryLanguage": "en-us",
            "captions": "extractive",
            "answers": "extractive",
            "top": k
        }
        if vector_search:
            search_payload["vectorQueries"]= [{"kind":"vector", "vector": query_vector, "fields": "contentVector","k": k, "exhaustive": "true"}]
            # search_payload["select"]= "id, title, chunk, name, location"
            search_payload["select"] =  str("id, title, content, chunk_id, url, filepath")
        else:
            #TODO: Fix this afterwards
            search_payload["select"] = str("id, title, chunks, language, name, location, vectorized")
        
        print(search_payload)
        print(json.dumps(search_payload))
        resp = requests.post(os.environ['AZURE_SEARCH_ENDPOINT'] + "/indexes/" + index + "/docs/search",
                         data=json.dumps(search_payload), headers=headers, params=params)

        search_results = resp.json()
        print('search results: ', search_results)
        agg_search_results[index] = search_results
    
    content = dict()
    ordered_content = OrderedDict()
    
    for index,search_results in agg_search_results.items():
        for result in search_results['value']:
            if result['@search.rerankerScore'] > reranker_threshold: # Show results that are at least N% of the max possible score=4
                content[result['id']]={
                                        "title": result['title'], 
                                        "name": result['filepath'], 
                                        "location": result['url'] + sas_token if result['url'] else "",
                                        "caption": result['@search.captions'][0]['text'],
                                        "index": index,
                                        "content": result["content"],
                                        "chunk_id": result['chunk_id']
                                    }
                if vector_search:
                    content[result['id']]["content"]= result['content']
                    content[result['id']]["score"]= result['@search.score'] # Uses the Hybrid RRF score
              
                else:
                    # content[result['id']]["chunks"]= result['chunks']
                    content[result['id']]["language"]= result['language']
                    content[result['id']]["score"]= result['@search.rerankerScore'] # Uses the reranker score
                    content[result['id']]["vectorized"]= result['vectorized']
                
    # After results have been filtered, sort and add the top k to the ordered_content
    if vector_search:
        topk = similarity_k
    else:
        topk = k*len(indexes)
        
    count = 0  # To keep track of the number of results added
    for id in sorted(content, key=lambda x: content[x]["score"], reverse=True):
        ordered_content[id] = content[id]
        count += 1
        if count >= topk:  # Stop after adding 5 results
            break

    return ordered_content

def create_llm():
    COMPLETION_TOKENS = 1000
    llm = AzureChatOpenAI(deployment_name="gpt-35-turbo-16k", temperature=0.5, max_tokens=COMPLETION_TOKENS, validate_base_url=False, openai_api_version="2023-05-15")
    return llm

def collate_processed_docs(ordered_results):
    top_docs = []
    for key,value in ordered_results.items():
        location = value["location"] if value["location"] is not None else ""
        # top_docs.append(Document(page_content=value["chunk"], metadata={"source": location+os.environ['BLOB_SAS_TOKEN']}))
        top_docs.append(Document(page_content=value["content"], metadata={"source": location}))

            
    print("Number of chunks:",len(top_docs))

def get_answer(question):
    # Calculate number of tokens of our docs
    llm = create_llm()
    combined_question_prompt, combined_prompt_template, combined_prompt = get_prompt_template()

    ordered_content = get_search_results(question, get_vector_profile_indices(), 
                                        k=10,
                                        reranker_threshold=1,
                                        vector_search=True, 
                                        similarity_k=10,
                                        query_vector = getmebedding(question)
                                        )
    top_docs = collate_processed_docs(ordered_content)
    if(len(top_docs)>0):
        tokens_limit = model_tokens_limit(MODEL) # this is a custom function we created in common/utils.py
        prompt_tokens = num_tokens_from_string(combined_prompt_template) # this is a custom function we created in common/utils.py
        context_tokens = num_tokens_from_docs(top_docs) # this is a custom function we created in common/utils.py
        
        requested_tokens = prompt_tokens + context_tokens + COMPLETION_TOKENS
        
        chain_type = "map_reduce" if requested_tokens > 0.9 * tokens_limit else "stuff"  
        
        print("System prompt token count:",prompt_tokens)
        print("Max Completion Token count:", COMPLETION_TOKENS)
        print("Combined docs (context) token count:",context_tokens)
        print("--------")
        print("Requested token count:",requested_tokens)
        print("Token limit for", MODEL, ":", tokens_limit)
        print("Chain Type selected:", chain_type)
            
    else:
        print("NO RESULTS FROM AZURE SEARCH")

    
    if chain_type == "stuff":
        chain = load_qa_with_sources_chain(llm, chain_type=chain_type, 
                                        prompt=combined_prompt)
    elif chain_type == "map_reduce":
        chain = load_qa_with_sources_chain(llm, chain_type=chain_type, 
                                        question_prompt=combined_question_prompt,
                                        combine_prompt=combined_prompt,
                                        return_intermediate_steps=True)
    response = chain({"input_documents": top_docs, "question": question, "language": "English"})
    return response