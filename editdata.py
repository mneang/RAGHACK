import json

# Load the JSON data
with open('azure_data.json', 'r', encoding='utf-8') as file:
    documents = json.load(file)

# Remove the "travel" field from each document
for doc in documents:
    if 'travel' in doc:
        del doc['travel']

# Save the modified documents back to a new file
with open('azure_data_final.json', 'w', encoding='utf-8') as output_file:
    json.dump(documents, output_file, ensure_ascii=False, indent=2)

print("File saved as 'azure_data_final.json'")
