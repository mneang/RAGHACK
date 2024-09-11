import requests
import json

# Define your Azure Cognitive Search details
endpoint = "https://raghack2024.search.windows.net"
index_name = "touristdata"
api_version = "2021-04-30-Preview"  # The version might change; adjust if necessary
api_key = "YTC2IuWkjdDzBprcW6pgp1n89EUoPYtn7RIMQ4PGG6AzSeCWP6u7"

# Define the search endpoint
url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"

# Define the headers and body for the search request
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}
body = {
    "search": "*",  # Wildcard search to fetch all documents
    "top": 1000  # Adjust the number of documents to fetch as needed
}

# Send the search request
response = requests.post(url, headers=headers, json=body)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()

    # Save the JSON data to a file
    with open("azure_data.json", "w") as json_file:
        json.dump(data['value'], json_file, indent=4)

    print("Data saved to 'azure_data.json'.")
else:
    print(f"Error: {response.status_code}, {response.text}")
