import logging
from fastapi import FastAPI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel
import requests

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
def fallback_response(query):
    fallback_responses = {
        "travel_advice": "Japan offers a variety of experiences, from the bustling streets of Tokyo to the serene temples of Kyoto. Be sure to explore!",
        "where_to_go": "If you're unsure where to start in Japan, I recommend visiting popular cities like Tokyo, Osaka, and Kyoto.",
        "what_to_do": "Japan offers a range of activities, from visiting historical sites to indulging in Japanese cuisine.",
        "food": "Japanese cuisine is world-renowned. Be sure to try sushi, ramen, tempura, and street food like takoyaki and okonomiyaki.",
        "general": "I'm here to help with travel advice about Japan. Please ask me about cities, landmarks, food, or the weather."
    }
    if "where" in query.lower() or "go" in query.lower():
        return fallback_responses["where_to_go"]
    elif "do" in query.lower() or "activities" in query.lower():
        return fallback_responses["what_to_do"]
    elif "food" in query or "eat" in query:
        return fallback_responses["food"]
    else:
        return fallback_responses["general"]
    
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

    is_japanese = any('\u4e00' <= char <= '\u9fff' for char in query)

    # If the query is in Japanese, translate it to English
    if is_japanese:
        logging.info("Japanese characters detected.")
        query = translate_text(query, to_language="en")
        logging.info(f"Translated query: {query}")

    # Handle general fallback cases for unrecognized or incomplete queries
    if len(query.split()) < 3:
        return {"message": "I'm here to provide advice about Japan travel. Please ask me your questions about cities, landmarks, food, or the weather."}

    # Fallback response for travel advice, where to go, or activities in Japan
    if "travel advice" in query:
        return {"message": "Japan offers a variety of experiences, from the bustling streets of Tokyo to the serene temples of Kyoto. Be sure to explore!"}
    elif "where should i go" in query or "where to go" in query:
        return {"message": "If you're unsure where to start in Japan, I recommend visiting popular cities like Tokyo, Osaka, and Kyoto."}
    elif "what to do" in query or "activities" in query:
        return {"message": "Japan offers a range of activities, from visiting historical sites to indulging in Japanese cuisine."}
    elif "travel" in query and not any(x in query for x in ["to", "from"]):
        return {"message": "Japan's transportation system is highly developed. You can travel between cities quickly using the Shinkansen (bullet train), planes, or buses."}


    # Perform search on Azure Cognitive Search
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

        # Handle weather queries
        if any(x in query for x in ["weather", "summer", "winter", "spring", "autumn", "fall"]):
            weather_info = format_weather(weather_data, query)
            response["message"] = f"{weather_info}"

        # Handle food queries specifically for the city in the search result
        elif "food" in query or "eat" in query:
            # Check if the query is about food in Japan (no city mentioned)
            if "japan" in query or "日本" in query:
                response["message"] = "Japanese cuisine is world-renowned. Be sure to try sushi, ramen, tempura, and street food like takoyaki and okonomiyaki."
            # If a specific city is mentioned, provide city-specific food info
            elif any(city in query for city in ["tokyo", "osaka", "kyoto", "nara", "hokkaido"]):
                response["message"] = f"{food_info}."
            # If no city is mentioned but there's food info, provide that city's food info
            else:
                response["message"] = f"Here is what {city.capitalize()} is famous for: {food_info}."


        # Handle landmark queries
        elif any(x in query for x in ["landmark", "sightseeing", "attraction", "must-see"]):
            if landmarks:
                landmark_list = "\n".join(landmarks)
                response["message"] = f"In {city}, some popular landmarks include:\n{landmark_list}"
            else:
                response["message"] = f"No specific landmarks found for {city}."

        # For general queries, return the description of the city
        else:
            response["message"] = description

        # Translate response back to Japanese if needed
        if is_japanese:
            logging.info("Translating response back to Japanese.")
            response["message"] = translate_response_to_japanese(response["message"])

        logging.info(f"Responding with: {response['message']}")
        return response
    else:
        # Use static fallback response if no search results are found
        fallback = fallback_response(query)
        return {"message": fallback}
