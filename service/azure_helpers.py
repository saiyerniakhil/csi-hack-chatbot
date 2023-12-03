import tiktoken
from langchain.prompts import PromptTemplate


# Returns the num of tokens used on a string
def num_tokens_from_string(string: str) -> int:
    encoding_name ='cl100k_base'
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# Returning the toekn limit based on model selection
def model_tokens_limit(model: str) -> int:
    """Returns the number of tokens limits in a text model."""
    if model == "gpt-35-turbo":
        token_limit = 4096
    elif model == "gpt-4":
        token_limit = 8192
    elif model == "gpt-35-turbo-16k":
        token_limit = 16384
    elif model == "gpt-4-32k":
        token_limit = 32768
    else:
        token_limit = 4096
    return token_limit

# Returns num of toknes used on a list of Documents objects
def num_tokens_from_docs(docs) -> int:
    num_tokens = 0
    for i in range(len(docs)):
        num_tokens += num_tokens_from_string(docs[i].page_content)
    return num_tokens


def get_prompt_template():


    COMBINE_QUESTION_PROMPT_TEMPLATE = """Use the following portion of a long document to see if any of the text is relevant to answer the question. 
    Return any relevant text in {language}.
    {context}
    Question: {question}
    Relevant text, if any, in {language}:"""

    COMBINE_QUESTION_PROMPT = PromptTemplate(
        template=COMBINE_QUESTION_PROMPT_TEMPLATE, input_variables=["context", "question", "language"]
    )


    COMBINE_PROMPT_TEMPLATE = """
    # Instructions:
    - Given the following extracted parts from one or multiple documents, and a question, create a final answer with references. 
    - You can only provide numerical references to documents, using this html format: `<sup><a href="url?query_parameters" target="_blank">[number]</a></sup>`.
    - The reference must be from the `Source:` section of the extracted part. You are not to make a reference from the content, only from the `Source:` of the extract parts.
    - Reference (source) document's url can include query parameters, for example: "https://example.com/search?query=apple&category=fruits&sort=asc&page=1". On these cases, **you must** include que query references on the document url, using this html format: <sup><a href="url?query_parameters" target="_blank">[number]</a></sup>.
    - **You can only answer the question from information contained in the extracted parts below**, DO NOT use your prior knowledge.
    - Never provide an answer without references.
    - If you don't know the answer, just say that you don't know. Don't try to make up an answer.
    - Respond in {language}.

    =========
    QUESTION: {question}
    =========
    {summaries}
    =========
    FINAL ANSWER IN {language}:"""


    COMBINE_PROMPT = PromptTemplate(
        template=COMBINE_PROMPT_TEMPLATE, input_variables=["summaries", "question", "language"]
    )
    return COMBINE_QUESTION_PROMPT,COMBINE_PROMPT_TEMPLATE,COMBINE_PROMPT

def get_vector_profile_indices():
    profile_index_name = "carpediemsearchindex"
    vector_indexes = [profile_index_name]
    return vector_indexes