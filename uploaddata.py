from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import json

# Replace with your actual values
endpoint = "https://raghack2024.search.windows.net"
api_key = "YTC2IuWkjdDzBprcW6pgp1n89EUoPYtn7RIMQ4PGG6AzSeCWP6u7"
index_name = "touristdata"

# Create a client to connect to the search service
search_client = SearchClient(endpoint=endpoint,
                             index_name=index_name,
                             credential=AzureKeyCredential(api_key))

# Read the JSON data file with UTF-8 encoding
with open('data.json', 'r', encoding='utf-8') as file:
    documents = json.load(file)

# Upload documents to the index
result = search_client.upload_documents(documents=documents)
print(f"Upload result: {result}")
