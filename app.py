import logging
from fastapi import FastAPI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel
import openai
import requests
from langdetect import detect


app = FastAPI()


# Azure Cognitive Search and OpenAI setup
search_client = SearchClient(
    endpoint="https://raghack2024.search.windows.net",
    index_name="touristdata",
    credential=AzureKeyCredential("YTC2IuWkjdDzBprcW6pgp1n89EUoPYtn7RIMQ4PGG6AzSeCWP6u7")
)


# Azure Translator setup
translator_key = "6636bb193d854b3fb496f9383050ed6f"
translator_region = "westus"
translator_endpoint = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"


openai.api_key = "2d53ea336c2d4bb39b0dc9bca16fe69c"


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
        "what_to_do": "Japan offers a range of activities, from visiting historical sites to indulging in Japanese cuisine."
    }
    if "where" in query.lower() or "go" in query.lower():
        return fallback_responses["where_to_go"]
    elif "do" in query.lower() or "activities" in query.lower():
        return fallback_responses["what_to_do"]
    else:
        return fallback_responses["travel_advice"]


# Generate LLM-based response if search fails
def generate_chat_response(prompt):
    response = openai.Completion.create(
        engine="chat",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()


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
# Modify the search function for edge case handling
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
        travel_data = first_result.get('travel', {})


        # Strictly handle weather queries
        if any(x in query for x in ["weather", "summer", "winter", "spring", "autumn", "fall"]):
            weather_info = format_weather(weather_data, query)
            response["message"] = f"The weather in {city} is:\n{weather_info}"


        # Handle food queries more specifically
        elif "food" in query or "eat" in query:
            response["message"] = f"{food_info}."


        # Handle travel queries dynamically
        elif "travel" in query or "go" in query:
            available_cities = ["tokyo", "kyoto", "osaka", "hokkaido", "nara", "fukuoka", "hiroshima", "nikko", "nagoya", "kobe"]
            origin_city = None
            destination_city = None


            for available_city in available_cities:
                if f"from {available_city}" in query:
                    origin_city = available_city
                if f"to {available_city}" in query:
                    destination_city = available_city


            if origin_city and destination_city:
                travel_key = f"from_{origin_city}"
                travel_info = travel_data.get(travel_key, f"No travel info available from {origin_city.capitalize()} to {destination_city.capitalize()}.")
                response["message"] = f"{travel_info}"
            else:
                response["message"] = f"No travel info available for the cities in your query."


        # For general queries, return the description of the city
        else:
            response["message"] = description


        # Ensure the message exists before translation
        if "message" in response:
            # Translate the response back to Japanese if the input was in Japanese
            if is_japanese:
                logging.info("Translating response back to Japanese.")
                response["message"] = translate_response_to_japanese(response["message"])
        else:
            response["message"] = "I'm sorry, I couldn't process your request."


        logging.info(f"Responding with: {response['message']}")
        return response
    else:
        # If no results, return a fallback response or generate an AI response
        fallback = fallback_response(query)
        generated_response = generate_chat_response(fallback)


        if is_japanese:
            generated_response = translate_response_to_japanese(generated_response)


        return {"message": generated_response}











