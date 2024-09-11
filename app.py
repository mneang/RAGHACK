import logging
from fastapi import FastAPI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel
import requests
from langdetect import detect, LangDetectException

app = FastAPI()

# Azure Cognitive Search setup
search_client = SearchClient(
    endpoint="https://raghack2024.search.windows.net",
    index_name="touristdata",
    credential=AzureKeyCredential("YTC2IuWkjdDzBprcW6pgp1n89EUoPYtn7RIMQ4PGG6AzSeCWP6u7")
)

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
        "general": "I'm here to help with travel advice about Japan. Please ask me about cities, landmarks, food, or the weather."
    }

    if "where" in query.lower() or "go" in query.lower():
        response = fallback_responses["where_to_go"]
    elif "do" in query.lower() or "activities" in query.lower():
        response = fallback_responses["what_to_do"]
    elif "food" in query or "eat" in query:
        response = fallback_responses["food"]
    else:
        response = fallback_responses["general"]

    # Translate fallback response to Japanese if the original query was in Japanese
    if is_japanese:
        response = translate_response_to_japanese(response)

    return response

# Helper to format weather info based on the specific season asked
def format_weather(weather_data, query):
    if "summer" in query:
        return weather_data.get('summer', 'No data available for summer.')
    elif "winter" in query:
        return weather_data.get('winter', 'No data available for winter.')
    elif "spring" in query:
        return weather_data.get('spring', 'No data available for spring.')
    elif "autumn" in query or "fall" in query:
        return weather_data.get('autumn', 'No data available for autumn.')
    else:
        return (f"Summer: {weather_data.get('summer', 'No information available.')}\n"
                f"Winter: {weather_data.get('winter', 'No information available.')}\n"
                f"Spring: {weather_data.get('spring', 'No information available.')}\n"
                f"Autumn: {weather_data.get('autumn', 'No information available.')}")


class SearchQuery(BaseModel):
    query: str

@app.post("/search")
async def search(search_query: SearchQuery):
    query = search_query.query.lower()
    logging.info(f"Received query: {query}")

    try:
        # Detect the language of the query
        detected_language = detect(query)
        logging.info(f"Detected language: {detected_language}")

        # If the language is not Japanese or English, return a specific message
        if detected_language not in ["en", "ja"]:
            return {"message": "Please use Japanese or English. 日本語か英語を使用してください。"}
    except LangDetectException:
        # Handle case where language detection fails (empty or ambiguous input)
        return {"message": "Unable to detect language. Please use Japanese or English.　言語を検出できませんでした。日本語か英語を使用してください。"}

    # Convert query to lowercase
    query = query.lower()

    is_japanese = detected_language == "ja"

    # If the query is in Japanese, translate it to English
    if is_japanese:
        logging.info("Japanese characters detected.")
        query = translate_text(query, to_language="en")
        logging.info(f"Translated query: {query}")

    # Check if the query mentions any city from the "toshi" list in either English or Japanese. "Toshi" (都市) means "city" in Japanese.
    city_mentioned = any(city in query for city in toshi) or any(city in search_query.query for city in toshi_jp)

    # If no city is mentioned, trigger the fallback response for general queries
    if not city_mentioned:
        return {"message": fallback_response(query, is_japanese)}

    # Perform search on Azure Cognitive Search if a city is mentioned
    search_results = search_client.search(search_text=query)
    search_results_list = list(search_results)

    if search_results_list:
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
        
        # Handle weather queries
        elif any(x in query for x in ["weather", "summer", "winter", "spring", "autumn", "fall"]):
            weather_info = format_weather(weather_data, query)
            response["message"] = f"{weather_info}"

        # Handle food queries specifically for the city in the search result
        elif any(x in query for x in ["food","eat","cuisine","gastronomy","rice"]):
            response["message"] = f"{food_info}."

        # Handle landmark queries
        elif any(x in query for x in ["landmark", "sightseeing", "attraction", "must-see", "famous", "sites", "history"]):
            if landmarks:
                landmark_list = "\n".join(landmarks)
                response["message"] = f"In {city}, some popular landmarks include:\n{landmark_list}"
            else:
                response["message"] = f"No specific landmarks found for {city}."

        # Translate response back to Japanese if needed
        if is_japanese:
            logging.info("Translating response back to Japanese.")
            response["message"] = translate_response_to_japanese(response["message"])

        logging.info(f"Responding with: {response['message']}")
        return response
    else:
        # Use static fallback response if no search results are found
        fallback = fallback_response(query, is_japanese)
        return {"message": fallback}

