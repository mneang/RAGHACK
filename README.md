# 🌸 Sakura Guide: AI-Powered Travel Assistant for Japan

## 1. Background + Overview 🚀

Exploring Japan should be about experiencing the culture, not worrying about how to navigate language barriers or drowning in an overwhelming amount of tourist information. **Sakura Guide** is here to solve those problems with **real-time, location-specific travel recommendations** in both English and Japanese.

Imagine walking through the streets of Tokyo, wondering what to do next. With *Sakura Guide*, you get **immediate**, tailored recommendations based on exactly where you are and what you want to experience.


### The Problem:
- **Language Barriers**: International tourists often struggle to find accurate, real-time information due to limited English-language resources.
- **Information Overload**: Domestic travelers, especially during peak times like **Golden Week**, are faced with too many choices and irrelevant suggestions.
- **Outdated Travel Guides**: Static guides can’t keep up with the changing pace of travel trends and tourist needs.

### Our Solution:
Powered by the latest in AI and cloud technology, **Sakura Guide** adapts to each traveler, offering dynamic, personalized recommendations and helping users experience Japan with ease. Whether you’re an international traveler looking for recommendations in English or a local navigating the crowded streets during peak travel seasons, *Sakura Guide* ensures you’re never stuck with outdated or irrelevant advice.

### User Query in Action 🎯
![query_eng](https://github.com/user-attachments/assets/4d9935f6-b114-4af7-a8f7-aa6113b15af4)
![query_jp](https://github.com/user-attachments/assets/cb7e5bf7-9131-47cd-9c24-006534789a99)
_The user asks for top recommendations in Kyoto, and Sakura Guide provides real-time, location-specific travel insights using Azure Cognitive Search._

---

## 2. Technology Architecture Overview 🛠️

Here’s what powers the **seamless experience** behind **Sakura Guide**:

- **FastAPI** ⚡: A lightweight, fast web framework that processes user queries instantly, ensuring a smooth, uninterrupted travel experience.
- **Azure Cognitive Search** 🔍: Delivers real-time travel recommendations by pulling the most relevant, up-to-date information about your location. It’s not just search—it’s about finding exactly what matters to the traveler.
- **Cosmos DB** 🗄️: Logs every user query, allowing us to learn from interactions and continuously improve. This helps **personalize future recommendations** and ensures that Sakura Guide gets smarter the more people use it.
- **Azure Translator** 🌐: Breaking down language barriers, this technology allows **Sakura Guide** to seamlessly switch between English and Japanese, ensuring inclusivity for both international and domestic tourists.

### Sakura Guide Technology Architecture 🏗️
![Sakura Guide pptx (6)](https://github.com/user-attachments/assets/f82d5894-232c-47d3-b517-01c8fe598427)
_A diagram illustrating how FastAPI, Azure Cognitive Search, Cosmos DB, and Azure Translator work together to provide seamless travel recommendations._

---

## 3. Executive Summary 💡

Imagine a travel assistant that understands not only where you are, but what you’re looking for—right now, in real time. That’s **Sakura Guide**.

By solving the key challenges travelers face in Japan, we’ve built a system that provides **immediate travel recommendations** in **English** and **Japanese**, using **AI-driven insights** from **Azure Cognitive Search**. Every query is logged in **Cosmos DB** to ensure that as more people use the app, it only gets better at providing **tailored advice**.

Whether it’s navigating Kyoto’s temples or finding the best ramen in Osaka, *Sakura Guide* is built to be **scalable, reliable**, and **ready for future personalization**.

---

## 4. Insights Deep Dive 🔍

### Instant, Location-Based Recommendations:
- **Sakura Guide** provides users with instant, **location-specific travel recommendations** based on their exact needs at that moment. For example, asking, *"What’s the best thing to do in Kyoto today?"* results in recommendations tailored specifically to your preferences.


### Azure Cognitive Search JSON Results 📊
![azureaisearch](https://github.com/user-attachments/assets/8a8513cc-c5b2-485f-9252-fd5ad776e763)

_Azure Cognitive Search JSON output for real-time travel recommendations. The app retrieves the most relevant travel data based on the user's location and query._

---

### Bilingual Experience 🌍
- By integrating **Azure Translator**, the app ensures that both English-speaking tourists and Japanese travelers have access to the same depth of information, removing language barriers from the travel experience entirely.

### Query Logging for Future Improvements 📈
- Every query is stored in **Cosmos DB**, enabling future versions of the app to offer **personalized recommendations** based on the user’s past interactions. Imagine an app that remembers the types of places you love—and gives you suggestions even before you ask.

### Cosmos DB Query Logs 🗄️
![cosmos db example](https://github.com/user-attachments/assets/7322ab3a-e329-430b-a844-c9faaca6bbd3)


_Example of user queries stored in Cosmos DB, allowing for personalized future recommendations based on interaction data._

---

### Intelligent Fallbacks:
- If a user asks a broad or vague question, like *"What should I do in Japan?"*, the app responds with **intelligent fallback suggestions**, guiding them toward the best activities and attractions.

---

## 5. Recommendations for the Future 📅

**Sakura Guide** is just getting started. Here’s what we’re planning for the future:

- **Personalization**: By analyzing the stored queries in **Cosmos DB**, we’ll introduce **personalized travel suggestions**, ensuring users receive recommendations that match their unique preferences.
- **Multi-Turn Conversations**: We’re adding support for interactive, follow-up conversations, making the travel planning process even more fluid and intuitive.
- **Scalability Across the Globe**: Built on scalable architecture, **Sakura Guide** is ready to expand beyond Japan and provide real-time, personalized travel experiences in any part of the world.


## 6. Caveats and Assumptions ⚠️

### Assumptions:
- The app currently operates using **English** and **Japanese**, with plans to expand into more languages in the future.
- **Cosmos DB** logging ensures the system can handle peak travel times, but further testing in real-world conditions will help refine performance during high-demand periods like **Golden Week**.

---

## 7. How to Set Up and Run Sakura Guide 🖥️

### Requirements:
- **Python 3.x**
- **FastAPI**
- **Azure SDK for Python**
- **Cosmos DB Account**
- **Azure Cognitive Search Account**

### Steps:
1. **Clone the Repository**:
   ```bash
   git clone <repository_url>

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt

3. **Run the Application**
   ```bash
   uvicorn app:app --reload

4. **Configure Cosmos DB and Azure Cognitive Search**:
   Ensure your Cosmos DB and Azure Cognitive Search accounts are set up and credentials are available as environment variables.

5. **Access the App**:
   Visit http://127.0.0.1:8000/ to interact with the app locally.

## 8. Final Thoughts 💭

At **Sakura Guide**, we believe that travel should be **seamless**, **intuitive**, and always **focused on the experience**—not the logistical headaches. Built with **passion** and **precision**, our app is designed to **grow, adapt**, and **continually improve** based on the needs of its users.

This isn’t just about getting information—it’s about **enhancing the travel experience**, making it more **accessible**, **personalized**, and **enjoyable** for anyone, anywhere.

