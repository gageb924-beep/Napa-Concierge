"""
Quick script to set up a test business for local development
Run this after starting the backend for the first time
"""

import requests

API_URL = "http://localhost:8000"
ADMIN_KEY = "admin_napa_concierge_2024"

# Create a test business
response = requests.post(
    f"{API_URL}/admin/businesses",
    headers={"X-Admin-Key": ADMIN_KEY},
    json={
        "name": "The Vineyard Inn",
        "business_type": "hotel",
        "primary_color": "#722F37",
        "welcome_message": "Welcome to The Vineyard Inn! I'm your personal Napa Valley concierge. I can help you plan wine tastings, book restaurant reservations, or discover hidden gems in wine country. What would you like to explore today?",
        "widget_title": "Vineyard Concierge",
        "widget_subtitle": "Your personal wine country guide",
        "custom_knowledge": """
The Vineyard Inn is a boutique hotel in the heart of Yountville.

Our amenities:
- 24 luxury rooms with vineyard views
- On-site restaurant "The Vine" serving farm-to-table cuisine
- Complimentary wine tasting every evening at 5pm
- Pool and spa facilities
- Free bicycle rentals for guests
- Partnerships with 20+ local wineries for exclusive tastings

Our room types:
- Garden View Room: $350/night
- Vineyard Suite: $550/night
- Grand Estate Suite: $850/night

Check-in: 3pm, Check-out: 11am

We're located at 1234 Wine Country Lane, Yountville, CA 94599
Phone: (707) 555-0123
"""
    }
)

if response.ok:
    data = response.json()
    print("\n" + "="*60)
    print("TEST BUSINESS CREATED!")
    print("="*60)
    print(f"\nBusiness: {data['name']}")
    print(f"API Key: {data['api_key']}")
    print("\nUpdate your frontend/demo.html with this API key:")
    print(f"  window.NAPA_CONCIERGE_KEY = '{data['api_key']}';")
    print("\n" + "="*60)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
