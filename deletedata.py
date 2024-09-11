# Replace with your actual values
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import json

# Credentials
endpoint = "https://raghack2024.search.windows.net"
api_key = "YTC2IuWkjdDzBprcW6pgp1n89EUoPYtn7RIMQ4PGG6AzSeCWP6u7"
index_name = "touristdata"

# Create a client to connect to the search service
search_client = SearchClient(endpoint=endpoint,
                             index_name=index_name,
                             credential=AzureKeyCredential(api_key))

# Read the JSON data file
with open('azure_data_final.json', 'r', encoding='utf-8') as file:
    documents = json.load(file)

# Ensure replacement behavior (by keeping the same IDs)
# Using mergeOrUpload ensures that it replaces documents with the same ID or adds if missing
for doc in documents:
    doc['@search.action'] = "mergeOrUpload"

# Upload or update documents in the index
result = search_client.upload_documents(documents=documents)
print(f"Upload result: {result}")
