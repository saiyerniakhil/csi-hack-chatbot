from openai import AzureOpenAI
import os

# openai.api_type = "azure"
# openai.api_key = os.environ["AZURE_OPENAI_API_KEY"]
# openai.api_base = os.environ["AZURE_OPENAI_ENDPOINT"]
# openai.api_version = "2023-05-15"
client = AzureOpenAI(
    # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#rest-api-versioning
    api_version="2023-07-01-preview",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    # https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
)

def getmebedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return list(list(dict(response)['data'][0]))[0][1]