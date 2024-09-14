import logging
from fastapi import FastAPI, Request
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel
import requests
from langdetect import detect, LangDetectException
from azure.cosmos import exceptions, CosmosClient, PartitionKey
import uuid
import datetime
import re
import gradio as gr


app = FastAPI()

# Azure Cognitive Search setup
search_client = SearchClient(
    endpoint="https://raghack2024.search.windows.net",
    index_name="touristdata",
    credential=AzureKeyCredential("YTC2IuWkjdDzBprcW6pgp1n89EUoPYtn7RIMQ4PGG6AzSeCWP6u7")
)



# Initialize Cosmos DB client
uri = "https://mneang.documents.azure.com:443/"
primary_key = "w8tf60FNU5oVrFjEK9hJbxhz3YoJaAd9MKQbb7eRXxiXqsYQG8WLyffxENYTAc9lmGizdtWNJ5WNACDbSnY3Xg=="
client = CosmosClient(uri, primary_key)

# Define database and container
database_name = "rag_database"
container_name = "user_queries"

# Create a database and container (only runs if they don't already exist)
try:
    database = client.create_database(database_name)
except exceptions.CosmosResourceExistsError:
    database = client.get_database_client(database_name)

try:
    container = database.create_container(id=container_name, partition_key=PartitionKey(path="/id"))
except exceptions.CosmosResourceExistsError:
    container = database.get_container_client(container_name)

# Function to add user query data to Cosmos DB
def add_query_to_cosmos(query_data):
    container.create_item(body=query_data)

# Azure Translator setup
translator_key = "6636bb193d854b3fb496f9383050ed6f"
translator_region = "westus"
translator_endpoint = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"

# List of cities in English and Japanese
toshi = ["tokyo", "osaka", "kyoto", "nara", "hokkaido", "nagoya", "fukuoka", "hiroshima", "nikko", "kobe"]
toshi_jp = ["東京", "大阪", "京都", "奈良", "北海道", "名古屋", "福岡", "広島", "日光", "神戸"]

# Translation function to handle non-English/Japanese inputs
def translate_text(text, to_language="en"):
    headers = {
        "Ocp-Apim-Subscription-Key": translator_key,
        "Ocp-Apim-Subscription-Region": translator_region,
        "Content-Type": "application/json"
    }
    body = [{"text": text}]
    url = f"{translator_endpoint}&to={to_language}"
    response = requests.post(url, headers=headers, json=body)
    response_json = response.json()
    return response_json[0]["translations"][0]["text"]

# Function to translate the response back to Japanese if the input was in Japanese
def translate_response_to_japanese(response):
    headers = {
        "Ocp-Apim-Subscription-Key": translator_key,
        "Ocp-Apim-Subscription-Region": translator_region,
        "Content-Type": "application/json"
    }
    body = [{"text": response}]
    url = f"{translator_endpoint}&to=ja"
    response = requests.post(url, headers=headers, json=body)
    response_json = response.json()
    return response_json[0]["translations"][0]["text"]

# Fallback response if search fails or query is too general
def fallback_response(query, is_japanese=False):
    fallback_responses = {
        "travel_advice": "Japan offers a variety of experiences, from the bustling streets of Tokyo to the serene temples of Kyoto. Be sure to explore!",
        "where_to_go": "If you're unsure where to start in Japan, I recommend visiting popular cities like Tokyo, Osaka, and Kyoto.",
        "what_to_do": "Japan offers a range of activities, from visiting historical sites to indulging in Japanese cuisine.",
        "food": "Japanese cuisine is world-renowned. Be sure to try sushi, ramen, tempura, and street food like takoyaki and okonomiyaki.",
        "general": "Japan offers a rich blend of modern and traditional experiences. From vibrant cities like Tokyo to serene temples in Kyoto, there's so much to explore. Feel free to ask about popular destinations, local cuisine, cultural landmarks, or seasonal weather!",
        "unrelated": "I'm here to help with travel advice about Japan. If you have any questions about cities, landmarks, food, or the weather, feel free to ask!"
    }

    if "where" in query.lower() or "go" in query.lower():
        response = fallback_responses["where_to_go"]
    elif any(keyword in query.lower() for keyword in ["do", "activities", "fun", "culture", "experience", "tour"]):
        response = fallback_responses["what_to_do"]
    elif any(keyword in query for keyword in ["food", "eat", "cuisine", "dishes", "gastronomy", "rice", "drink"]):
        response = fallback_responses["food"]
    elif any(keyword in query for keyword in ["japan", "city", "landmark", "weather", "travel", "sightseeing", "know", "general"]):
        response = fallback_responses["general"]
    else:
        # If query is unrelated or random
        response = fallback_responses["unrelated"]

    # Translate fallback response to Japanese if the original query was in Japanese
    if is_japanese:
        response = translate_response_to_japanese(response)

    return response

# Helper to provide a general weather overview for each city
def get_weather_overview(weather_data):
    return (f"Here's the general weather overview for this city:\n"
            f"Summer: {weather_data.get('summer', 'No data available for summer.')}\n"
            f"Winter: {weather_data.get('winter', 'No data available for winter.')}\n"
            f"Spring: {weather_data.get('spring', 'No data available for spring.')}\n"
            f"Autumn: {weather_data.get('autumn', 'No data available for autumn.')}")

class SearchQuery(BaseModel):
    query: str

@app.post("/search")
async def search(search_query: SearchQuery, request:Request):
    query = search_query.query.lower()
    logging.info(f"Received query: {query}")

    user_id = request.client.host  # We are using IP address as user ID for simplicity

    try:
            # Detect the language of the query
            detected_language = detect(query)
            logging.info(f"Detected language: {detected_language}")

            # If the language is not Japanese or English, return a specific message
            if detected_language not in ["en", "ja"]:
                # Fallback: If the query is ASCII and short, treat it as English
                if query.isascii() and len(query.split()) > 1:
                    detected_language in ["en"]  # Assume it's English
                else:
                    return {"message": "Please use Japanese or English. 日本語か英語を使用してください。"}
    except LangDetectException:
            # Handle case where language detection fails (empty or ambiguous input)
            return {"message": "Unable to detect language. Please use Japanese or English. 言語を検出できませんでした。日本語か英語を使用してください。"}

    is_japanese = detected_language == "ja"

    # If the query is in Japanese, translate it to English
    if is_japanese:
        logging.info("Japanese characters detected.")
        query = translate_text(query, to_language="en")
        logging.info(f"Translated query: {query}")

# Store the query in Cosmos DB
    query_data = {
        "id": str(uuid.uuid4()),  # Unique ID for each query
        "query": query,
        "timestamp": str(datetime.datetime.utcnow())
    }
    add_query_to_cosmos(query_data)  # Storing query into Cosmos DB

    # Check if the query mentions any city from the "toshi" list in either English or Japanese. "Toshi" (都市) means "city" in Japanese.
    city_mentioned = any(city in query for city in toshi) or any(city in search_query.query for city in toshi_jp)

# If a city is mentioned and the query is vague　return the city description
    if city_mentioned and len(query.split()) == 1:
        for city in toshi:
            if city in query:
                first_result = search_client.search(search_text=city)
                city_description = first_result['description']
                return {"message": city_description}

    # If no city is mentioned, trigger the fallback response for general queries
    if not city_mentioned:
        return {"message": fallback_response(query, is_japanese)}

    try:
            search_results = search_client.search(search_text=query)
            search_results_list = list(search_results)
    except Exception as e:
            logging.error(f"Search query failed: {e}")  # Log the specific error
            return {"message": "Search service is currently unavailable."}  # Handle search failure gracefully


    if search_results_list:
        response = {"message": "", "followup": ""}
        first_result = search_results_list[0]
        logging.info(f"Full search result: {first_result}")

        response = {}
        city = first_result['city']
        description = first_result.get('description', 'No description available.')
        food_info = first_result.get('food', 'No food info available.')
        weather_data = first_result.get('weather', {})
        landmarks = first_result.get('landmarks', [])

        # If the query mentions a city but doesn't specify a category, return the city description
        if not any(x in query for x in ["weather", "food", "landmark", "sightseeing", "attraction", "must-see", "eat"]):
            response["message"] = description

             # Suggest follow-up questions about the city
            response["followup"] = "Want more travel advice? Visit Japan's official tourism website: https://www.japan.travel/en/"
        
       # Handle weather queries specifically for the city in the search result
        elif "weather" in query or any(season in query for season in ["summer", "winter", "spring", "autumn", "fall"]):
            # Return the general weather overview for the city
            weather_info = get_weather_overview(weather_data)
            response["message"] = weather_info
            response["followup"] = f"Get a live weather forecast for {city} at Weather.com: https://weather.com"


        # Handle food queries specifically for the city in the search result
        elif any(x in query for x in ["food","eat","cuisine","gastronomy","rice"]):
            response["message"] = f"{food_info}.".strip()

            response["followup"] = f"Want more restaurant options? Check Yelp for {city}: https://www.yelp.com/search?find_desc=restaurants&find_loc={city}"

        # Handle landmark queries
        elif any(x in query for x in ["landmark", "sightseeing", "attraction", "must-see", "famous", "sites", "history"]):
            if landmarks:
                landmark_list = "\n".join(landmarks)
                response["message"] = f"In {city}, some popular landmarks include:\n{landmark_list}"
            else:
                response["message"] = f"Sorry, no specific landmarks found for {city}."

            response["followup"] = f"Explore these landmarks on Google Maps: https://www.google.com/maps/search/{city}+landmarks"

        # Translate response back to Japanese if needed
        if is_japanese:
            logging.info("Translating response back to Japanese.")
            response["message"] = translate_response_to_japanese(response["message"])
            response["followup"] = translate_response_to_japanese(response["followup"])

        logging.info(f"Responding with: {response['message']}")
        return response
    else:
        # Use static fallback response if no search results are found
        fallback = fallback_response(query, is_japanese)
        return {"message": fallback}

@app.post("/end-session")
async def end_session(request: Request):
    user_id = request.client.host  # Using IP address as a simple user ID
    
    # Store session end data in Cosmos DB
    session_end_data = {
        "id": str(uuid.uuid4()),  # Unique ID for the session end
        "user_id": user_id,
        "event": "session_end",
        "timestamp": str(datetime.datetime.utcnow())
    }
    add_query_to_cosmos(session_end_data)  # Store session end event
    
    # Return a final message
    return {"message": "Thank you for using our service! ご利用いただきありがとうございます。"}

@app.get("/")
async def root():
    return {"message": "FastAPI is running."}

# Gradio interface function: combine the message and follow-up clearly
def chatbot_interface(query):
    try:
        response = requests.post("http://127.0.0.1:8000/search", json={"query": query})
        response_data = response.json()

        # Combine message and followup, ensure no truncation or extra spaces
        message = response_data.get("message", "No response received")
        followup = response_data.get("followup", "").strip()

        # Return a combined response
        return f"{message}\n\n{followup}"  # Add spacing between the message and followup for clarity
    except Exception as e:
        return f"Error: {e}"

# Gradio interface with bilingual labels and a subtitle reminder
iface = gr.Interface(fn=chatbot_interface, 
                     inputs=gr.Textbox(label="Enter Query | クエリを入力", lines=2),  # Bilingual label for "Enter Query"
                     outputs=gr.Textbox(label="Output | 出力", lines=10, max_lines=20),  # Bilingual label for "Output"
                     title="Sakura Guide | さくらガイド",  # Bilingual title
                     description="Please enter queries in either English or Japanese. | 英語か日本語を使用してください。")  # Subtitle reminding language preference

# Launch Gradio interface only
if __name__ == "__main__":
    iface.launch(share=True)
