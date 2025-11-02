"""
Example usage of the integration layer in EcomoveX services.
This file demonstrates how to use the API clients in your service layer.
"""

import asyncio
from integration.map_api import GoogleMapsClient, get_maps_client
from integration.chatbot_api import ChatbotHelper, OpenAIClient
from integration.carbon_api import CustomCarbonCalculator, CarbonInterfaceClient


# ============================================================================
# Example 1: Using Google Maps API in Recommendation Service
# ============================================================================

async def example_recommendation_service():
    """How to use Google Maps in your recommendation service."""
    
    # Get eco-friendly places near a location
    async with GoogleMapsClient() as maps:
        # User's current location (e.g., Paris)
        latitude = 48.8566
        longitude = 2.3522
        
        # Find eco-friendly restaurants
        restaurants = await maps.search_nearby_places(
            latitude=latitude,
            longitude=longitude,
            radius=3000,
            place_type="restaurant",
            keyword="organic"
        )
        
        print(f"Found {len(restaurants.get('results', []))} organic restaurants")
        
        # Find bike rental shops
        bikes = await maps.search_nearby_places(
            latitude=latitude,
            longitude=longitude,
            radius=5000,
            place_type="bicycle_store"
        )
        
        print(f"Found {len(bikes.get('results', []))} bike rental shops")
        
        # Use the helper method for all eco-friendly places
        eco_places = await maps.find_eco_friendly_places(
            latitude=latitude,
            longitude=longitude,
            radius=5000
        )
        
        print(f"Found {len(eco_places)} total eco-friendly places")
        
        # Get place details
        if eco_places:
            place_id = eco_places[0].get('place_id')
            details = await maps.get_place_details(
                place_id=place_id,
                fields=["name", "rating", "formatted_address", "opening_hours"]
            )
            print(f"Place details: {details}")


# ============================================================================
# Example 2: Using Chatbot API in Chatbot Service
# ============================================================================

async def example_chatbot_service():
    """How to use AI chatbot in your chatbot service."""
    
    # Using the pre-configured eco-travel assistant
    chatbot = ChatbotHelper(provider="openai")  # or "gemini"
    
    # Get eco-travel advice
    user_message = "What are the most sustainable ways to travel in Europe?"
    
    response = await chatbot.get_eco_travel_response(
        user_message=user_message,
        conversation_history=[]
    )
    
    print(f"Bot: {response}")
    
    # Continue the conversation
    conversation_history = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]
    
    follow_up = "What about carbon emissions for trains vs planes?"
    response2 = await chatbot.get_eco_travel_response(
        user_message=follow_up,
        conversation_history=conversation_history
    )
    
    print(f"Bot: {response2}")
    
    await chatbot.close()


async def example_custom_chatbot():
    """Direct usage of OpenAI client for custom chatbot behavior."""
    
    async with OpenAIClient() as client:
        messages = [
            {
                "role": "system",
                "content": "You are a travel expert specializing in sustainable tourism."
            },
            {
                "role": "user",
                "content": "Recommend a 3-day eco-friendly itinerary in Amsterdam"
            }
        ]
        
        # Non-streaming response
        response = await client.chat_completion(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        answer = response["choices"][0]["message"]["content"]
        print(f"Itinerary:\n{answer}")


# ============================================================================
# Example 3: Using Carbon API in Carbon Service
# ============================================================================

async def example_carbon_service():
    """How to calculate carbon emissions in your carbon service."""
    
    calculator = CustomCarbonCalculator()
    
    # Calculate emissions for a trip from Paris to Rome
    
    # Option 1: Flight
    flight_emissions = calculator.calculate_flight_emissions(
        distance_km=1100,
        cabin_class="economy",
        passengers=1
    )
    print(f"Flight emissions: {flight_emissions} kg CO2")
    
    # Option 2: Train
    train_emissions = calculator.calculate_transport_emissions(
        transport_mode="train",
        distance_km=1100,
        passengers=1
    )
    print(f"Train emissions: {train_emissions} kg CO2")
    
    # Option 3: Electric car
    car_emissions = calculator.calculate_transport_emissions(
        transport_mode="car_electric",
        distance_km=1100,
        passengers=1
    )
    print(f"Electric car emissions: {car_emissions} kg CO2")
    
    # Compare all options
    comparison = calculator.compare_transport_options(
        distance_km=1100,
        transport_modes=["flight_economy", "train", "car_electric", "car_gasoline"]
    )
    print(f"\nEmissions comparison:")
    for mode, emissions in sorted(comparison.items(), key=lambda x: x[1]):
        print(f"  {mode}: {emissions} kg CO2")
    
    # Calculate eco score
    eco_score = calculator.get_eco_score(train_emissions)
    print(f"\nEco Score for train: {eco_score['score']}/100 ({eco_score['rating']})")
    print(f"Recommendations: {', '.join(eco_score['recommendations'])}")


async def example_carbon_interface_api():
    """Using the Carbon Interface API for real-time data."""
    
    async with CarbonInterfaceClient() as client:
        # Calculate flight emissions
        flight = await client.estimate_flight_emissions(
            passengers=2,
            departure_airport="CDG",  # Paris Charles de Gaulle
            destination_airport="FCO",  # Rome Fiumicino
            cabin_class="economy"
        )
        
        emissions_kg = flight["data"]["attributes"]["carbon_kg"]
        print(f"Flight emissions (API): {emissions_kg} kg CO2")
        
        # Calculate car trip emissions
        car = await client.estimate_vehicle_emissions(
            distance_value=150,
            distance_unit="km",
            vehicle_make="Tesla",
            vehicle_model="Model 3",
            vehicle_year=2023
        )
        
        car_emissions = car["data"]["attributes"]["carbon_kg"]
        print(f"Car emissions (API): {car_emissions} kg CO2")


# ============================================================================
# Example 4: Complete Trip Planning Flow
# ============================================================================

async def example_complete_trip_planning():
    """
    Complete example: Plan an eco-friendly trip using all APIs.
    This shows how to integrate all services together.
    """
    
    print("=== Planning an Eco-Friendly Trip ===\n")
    
    # Step 1: Get user's destination
    origin = "Paris, France"
    destination = "Lyon, France"
    
    # Step 2: Calculate route and emissions
    async with GoogleMapsClient() as maps:
        # Get directions for different modes
        print("1. Calculating routes...")
        
        train_route = await maps.get_directions(
            origin=origin,
            destination=destination,
            mode="transit"
        )
        
        car_route = await maps.get_directions(
            origin=origin,
            destination=destination,
            mode="driving"
        )
        
        if train_route.get("routes"):
            distance_km = train_route["routes"][0]["legs"][0]["distance"]["value"] / 1000
            duration = train_route["routes"][0]["legs"][0]["duration"]["text"]
            print(f"   Distance: {distance_km:.1f} km")
            print(f"   Duration: {duration}")
        
        # Step 3: Calculate carbon footprint
        print("\n2. Calculating carbon emissions...")
        calculator = CustomCarbonCalculator()
        
        emissions = calculator.compare_transport_options(
            distance_km=distance_km,
            transport_modes=["train", "car_electric", "car_gasoline", "flight_economy"]
        )
        
        for mode, co2 in emissions.items():
            score = calculator.get_eco_score(co2)
            print(f"   {mode}: {co2} kg CO2 (Score: {score['score']}/100)")
        
        # Step 4: Find eco-friendly accommodations
        print("\n3. Finding eco-friendly hotels in Lyon...")
        
        # Geocode Lyon to get coordinates
        lyon_coords = await maps.geocode_address("Lyon, France")
        if lyon_coords.get("results"):
            lat = lyon_coords["results"][0]["geometry"]["location"]["lat"]
            lng = lyon_coords["results"][0]["geometry"]["location"]["lng"]
            
            # Search for eco-friendly hotels
            hotels = await maps.search_nearby_places(
                latitude=lat,
                longitude=lng,
                radius=5000,
                place_type="lodging",
                keyword="eco"
            )
            
            print(f"   Found {len(hotels.get('results', []))} eco-friendly hotels")
        
        # Step 5: Get AI recommendations
        print("\n4. Getting personalized recommendations from AI...")
        
    chatbot = ChatbotHelper(provider="openai")
    
    ai_prompt = f"""I'm planning a trip from {origin} to {destination}.
The train trip is {distance_km:.1f} km and produces {emissions['train']} kg CO2.
Give me 3 tips for making this trip more sustainable."""
    
    recommendations = await chatbot.get_eco_travel_response(ai_prompt)
    print(f"   {recommendations}")
    
    await chatbot.close()
    
    print("\n=== Trip Planning Complete! ===")


# ============================================================================
# Run Examples
# ============================================================================

async def main():
    """Run all examples."""
    
    print("=" * 70)
    print("EXAMPLE 1: Recommendation Service (Maps API)")
    print("=" * 70)
    await example_recommendation_service()
    
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Chatbot Service")
    print("=" * 70)
    # await example_chatbot_service()  # Uncomment if you have API keys
    
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Carbon Service")
    print("=" * 70)
    await example_carbon_service()
    
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Complete Trip Planning")
    print("=" * 70)
    # await example_complete_trip_planning()  # Uncomment if you have API keys


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
    
    # Or run individual examples:
    # asyncio.run(example_recommendation_service())
    # asyncio.run(example_chatbot_service())
    # asyncio.run(example_carbon_service())
    # asyncio.run(example_complete_trip_planning())
