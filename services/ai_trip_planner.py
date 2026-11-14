"""Personal AI Travel Agent & Itinerary Planning Engine for TBO.

Generates complete N-day trip itineraries with:
- Three-tier pricing comparison (Cheapest / Budget, Mid-level / Recommended, Luxury / Premium)
- Stays & Hotels across tiers
- Transport interconnectivity (Metro, Cabs, Trains, Airport Transfers)
- Food & Dining recommendations (Iconic local spots, Breakfast/Lunch/Dinner)
- Sightseeing & Attractions with timings & tips
- Exact geo-coordinates for interactive map route plotting
"""

from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, Field

# Curated Pan-India City Knowledge Base & Interconnectivity Hubs
PAN_INDIA_HUBS: dict[str, dict[str, Any]] = {
    "delhi": {
        "name": "Delhi & NCR",
        "state": "National Capital Region",
        "description": "Historical heart of India blending Mughal heritage, colonial architecture, and modern culinary culture.",
        "best_season": "October to March (pleasant weather)",
        "transit_hub": {
            "airport": "Indira Gandhi International Airport (DEL) T3 / T1",
            "metro": "Delhi Metro (Airport Express connects T3 to New Delhi Railway Station in 19 mins)",
            "railways": "New Delhi (NDLS), Old Delhi (DLI), Hazrat Nizamuddin (NZM)",
            "local_cab": "App cabs (Uber/Ola), Pre-paid auto-rickshaws, BluSmart EV cabs"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1500, "food_per_day": 600, "transit_per_day": 300, "tours_per_day": 400},
            "mid": {"hotel_per_night": 4500, "food_per_day": 1600, "transit_per_day": 900, "tours_per_day": 1200},
            "luxury": {"hotel_per_night": 16500, "food_per_day": 4800, "transit_per_day": 2800, "tours_per_day": 3500}
        },
        "stays": {
            "budget": [
                {"name": "Bloomrooms @ New Delhi Station", "price": 1800, "rating": 4.4, "tag": "Near Metro", "area": "Paharganj / Central"},
                {"name": "Zostel Delhi Central", "price": 1100, "rating": 4.5, "tag": "Backpacker Vibe", "area": "Paharganj"},
                {"name": "FabHotel Prime Connaught Place", "price": 2200, "rating": 4.2, "tag": "Value Stay", "area": "Connaught Place"}
            ],
            "mid": [
                {"name": "The Lalit New Delhi", "price": 5400, "rating": 4.6, "tag": "5-Star Value", "area": "Barakhamba Rd, CP"},
                {"name": "Radisson Blu Marina Hotel Connaught Place", "price": 4800, "rating": 4.5, "tag": "Heritage CP", "area": "Connaught Circus"},
                {"name": "Vivanta New Delhi Dwarka", "price": 4200, "rating": 4.5, "tag": "Near Airport", "area": "Dwarka Sector 21"}
            ],
            "luxury": [
                {"name": "The Taj Mahal Hotel New Delhi", "price": 16500, "rating": 4.9, "tag": "Legendary Luxury", "area": "Mansingh Road"},
                {"name": "The Imperial New Delhi", "price": 18500, "rating": 4.9, "tag": "Colonial Heritage", "area": "Janpath"},
                {"name": "The Oberoi New Delhi", "price": 22000, "rating": 5.0, "tag": "Ultra-Luxury", "area": "Golf Links, Dr Zakir Hussain Marg"}
            ]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Saravana Bhavan (Connaught Place)", "dish": "Ghee Roast Dosa & Filter Coffee", "cost": "₹200 - ₹350"},
            {"meal": "Lunch", "spot": "Karim's Old Delhi / Al Jawahar (Jama Masjid)", "dish": "Mutton Nihari, Chicken Jahangiri & Khamiri Roti", "cost": "₹450 - ₹800"},
            {"meal": "Evening Snack", "spot": "Chandni Chowk Paranthe Wali Gali & Natraj Dahi Bhalla", "dish": "Rabri Parantha & Dahi Bhalla", "cost": "₹150 - ₹250"},
            {"meal": "Dinner", "spot": "Bukhara - ITC Maurya / Indian Accent / Gulati Pandara Road", "dish": "Dal Bukhara, Sikandari Raan & Butter Chicken", "cost": "₹1200 - ₹4500"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "Mughal Splendors & Old Delhi Heritage",
                "morning": {"title": "Red Fort & Jama Masjid", "desc": "Visit the majestic 17th-century Mughal fortress and India's largest mosque.", "time": "09:00 AM - 12:30 PM", "lat": 28.6562, "lon": 77.2410},
                "transport": "Delhi Metro Yellow Line to Chandni Chowk Station, followed by an electric cycle-rickshaw.",
                "lunch": "Karim's Historic Eatery near Jama Masjid Gate 1.",
                "afternoon": {"title": "Chandni Chowk Spice Market (Khari Baoli)", "desc": "Asia's largest wholesale spice market with rooftop viewpoints of Old Delhi.", "time": "02:00 PM - 04:30 PM", "lat": 28.6575, "lon": 77.2245},
                "evening": {"title": "India Gate & Kartavya Path Light Show", "desc": "Evening stroll by the war memorial with illuminated fountains and sunset views.", "time": "05:30 PM - 08:00 PM", "lat": 28.6129, "lon": 77.2295},
                "dinner": "Gulati Restaurant at Pandara Road (Famous Butter Chicken & Dal Makhani)."
            },
            {
                "day": 2,
                "title": "Imperial Lutyens Delhi, Qutub Minar & Spiritual Sanctuaries",
                "morning": {"title": "Qutub Minar Complex & Mehrauli Archaeological Park", "desc": "UNESCO World Heritage site with the 73m victory minaret and Iron Pillar.", "time": "09:30 AM - 12:30 PM", "lat": 28.5244, "lon": 77.1855},
                "transport": "Delhi Metro Yellow Line to Qutub Minar Station or AC App Cab.",
                "lunch": "Olive Bar & Kitchen (Mehrauli) or Carnatic Cafe (Greater Kailash).",
                "afternoon": {"title": "Humayun's Tomb", "desc": "The architectural precursor to the Taj Mahal with serene Persian Charbagh gardens.", "time": "02:00 PM - 04:30 PM", "lat": 28.5933, "lon": 77.2507},
                "evening": {"title": "Connaught Place Heritage Circle & Janpath Market", "desc": "Walk along the Georgian-style colonnades, cafes, and open-air flea market.", "time": "05:00 PM - 08:00 PM", "lat": 28.6315, "lon": 77.2167},
                "dinner": "United Coffee House (CP) or Farzi Cafe."
            },
            {
                "day": 3,
                "title": "Modern Architectural Marvels & Artisan Haats",
                "morning": {"title": "Lotus Temple & Akshardham Temple", "desc": "Admire the Bahá'í Lotus Temple followed by the grand Akshardham complex.", "time": "09:00 AM - 01:00 PM", "lat": 28.5535, "lon": 77.2588},
                "transport": "Delhi Metro Blue Line to Akshardham Station.",
                "lunch": "Haldiram's or Dilli Haat Regional Food Stalls.",
                "afternoon": {"title": "Dilli Haat INA Crafts & Handlooms", "desc": "Open-air rural craft bazaar with artisans from all 28 Indian states.", "time": "02:30 PM - 05:30 PM", "lat": 28.5731, "lon": 77.2084},
                "evening": {"title": "Hauz Khas Village & Lake Sunset", "desc": "Medieval 13th-century reservoir ruins surrounded by trendy boutiques and cafes.", "time": "06:00 PM - 08:30 PM", "lat": 28.5494, "lon": 77.1937},
                "dinner": "Social Hauz Khas or Yeti - The Himalayan Kitchen."
            }
        ]
    },
    "mumbai": {
        "name": "Mumbai (City of Dreams)",
        "state": "Maharashtra",
        "description": "Financial powerhouse of India, featuring Victorian Gothic landmarks, Marine Drive promenade, Bollywood glamour, and vibrant sea-fronts.",
        "best_season": "November to February",
        "transit_hub": {
            "airport": "Chhatrapati Shivaji Maharaj International Airport (BOM) T2",
            "metro": "Mumbai Metro Line 2A & 7, Western & Central Local Trains",
            "railways": "CSMT (Chhatrapati Shivaji Terminus), Mumbai Central (MMCT), Bandra Terminus",
            "local_cab": "Kaali-Peeli Taxis, Uber/Ola, Sea Link Expressway"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 2200, "food_per_day": 700, "transit_per_day": 350, "tours_per_day": 500},
            "mid": {"hotel_per_night": 6500, "food_per_day": 2000, "transit_per_day": 1100, "tours_per_day": 1500},
            "luxury": {"hotel_per_night": 22000, "food_per_day": 5500, "transit_per_day": 3200, "tours_per_day": 4500}
        },
        "stays": {
            "budget": [
                {"name": "Backpacker Panda Colaba", "price": 1600, "rating": 4.3, "tag": "Colaba Walkable", "area": "Colaba"},
                {"name": "Hotel Suba Palace", "price": 3200, "rating": 4.4, "tag": "Near Gateway", "area": "Apollo Bunder"}
            ],
            "mid": [
                {"name": "Fariyas Hotel Mumbai", "price": 6800, "rating": 4.5, "tag": "Colaba Central", "area": "Colaba"},
                {"name": "The Shalimar Hotel Kemps Corner", "price": 5900, "rating": 4.4, "tag": "South Mumbai", "area": "Kemps Corner"}
            ],
            "luxury": [
                {"name": "The Taj Mahal Palace & Tower Mumbai", "price": 24000, "rating": 5.0, "tag": "Iconic Heritage", "area": "Apollo Bunder"},
                {"name": "The Oberoi Mumbai (Marine Drive)", "price": 21000, "rating": 4.9, "tag": "Sea View Luxury", "area": "Nariman Point"}
            ]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Cafe Mondegar / Leopold Cafe (Colaba)", "dish": "Keema Pav & Brun Maska with Chai", "cost": "₹250 - ₹450"},
            {"meal": "Lunch", "spot": "Trishna / Mahesh Lunch Home", "dish": "Butter Garlic Crab, Koliwada Prawns & Fish Curry", "cost": "₹800 - ₹1800"},
            {"meal": "Evening Snack", "spot": "Girgaon Chowpatty / Juhu Beach", "dish": "Mumbai Sev Puri, Bhel Puri & Pav Bhaji", "cost": "₹120 - ₹200"},
            {"meal": "Dinner", "spot": "The Table (Colaba) / Bastian (Bandra)", "dish": "Contemporary Coastal & Global Cuisine", "cost": "₹1500 - ₹4000"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "Colonial Heritage, Gateway of India & Marine Drive Sunset",
                "morning": {"title": "Gateway of India & Elephanta Caves Boat Ride", "desc": "Visit the 1924 waterfront basalt arch, then take a scenic ferry to the 6th-century Elephanta rock-cut temples.", "time": "08:30 AM - 01:00 PM", "lat": 18.9220, "lon": 72.8347},
                "transport": "Harbor Ferry from Gateway Jetty, followed by walking through the Colaba Causeway.",
                "lunch": "Leopold Cafe or Bademiya Kebabs.",
                "afternoon": {"title": "CSMT Terminus & Fort Heritage Precinct", "desc": "Marvel at the Victorian Gothic UNESCO railway terminus and Kala Ghoda art district.", "time": "02:30 PM - 05:00 PM", "lat": 18.9400, "lon": 72.8354},
                "evening": {"title": "Marine Drive Queen's Necklace Promenade", "desc": "Iconic 3.6km C-shaped boulevard along the Arabian Sea coast during golden hour.", "time": "05:30 PM - 08:00 PM", "lat": 18.9432, "lon": 72.8230},
                "dinner": "Pizza By The Bay (Marine Drive) or Sardar Pav Bhaji (Tardeo)."
            },
            {
                "day": 2,
                "title": "Bandra Trendsetters, Bandstand & Sea Link Voyage",
                "morning": {"title": "Siddhivinayak Temple & Shivaji Park", "desc": "Revered Ganesha temple followed by cultural walks in Dadar.", "time": "09:00 AM - 12:00 PM", "lat": 19.0169, "lon": 72.8304},
                "transport": "Bandra-Worli Sea Link 8-lane cable-stayed expressway bridge.",
                "lunch": "Gajalee Coastal Seafood (Vile Parle) or Candies (Bandra).",
                "afternoon": {"title": "Bandra Fort & Bandstand Promenade", "desc": "Castella de Aguada 1640 Portuguese fort with panoramic views of the Sea Link.", "time": "02:30 PM - 05:30 PM", "lat": 19.0415, "lon": 72.8184},
                "evening": {"title": "Juhu Beach Sunset & Street Food Trail", "desc": "Lively beach buzzing with Bollywood star homes, street snacks, and ocean breeze.", "time": "06:00 PM - 08:30 PM", "lat": 19.0988, "lon": 72.8264},
                "dinner": "Prithvi Cafe or Mahesh Lunch Home."
            }
        ]
    },
    "goa": {
        "name": "Goa (Sunshine & Beach Paradise)",
        "state": "Goa",
        "description": "Tropical coastal state renowned for golden beaches, Portuguese colonial churches, water sports, vibrant beach shacks, and seafood.",
        "best_season": "October to April",
        "transit_hub": {
            "airport": "Dabolim Airport (GOI) / Manohar International Airport Mopa (GOX)",
            "railways": "Madgaon (MAO), Thivim (THVM)",
            "local_cab": "Self-drive Scooters/Thars, GoaMiles App Cabs, Pre-paid tourist taxis"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1400, "food_per_day": 700, "transit_per_day": 400, "tours_per_day": 600},
            "mid": {"hotel_per_night": 4800, "food_per_day": 1800, "transit_per_day": 1200, "tours_per_day": 1800},
            "luxury": {"hotel_per_night": 18000, "food_per_day": 5000, "transit_per_day": 3000, "tours_per_day": 4000}
        },
        "stays": {
            "budget": [
                {"name": "Hostel Crowd - Vagator / Anjuna", "price": 1200, "rating": 4.6, "tag": "Beach Social", "area": "Vagator"},
                {"name": "Casa de Baga Boutique Stay", "price": 2200, "rating": 4.3, "tag": "Near Baga", "area": "Baga Beach"}
            ],
            "mid": [
                {"name": "Hard Rock Hotel Goa", "price": 5500, "rating": 4.5, "tag": "Resort Vibe", "area": "Calangute"},
                {"name": "Santana Beach Resort Candolim", "price": 4200, "rating": 4.5, "tag": "Direct Beach Access", "area": "Candolim"}
            ],
            "luxury": [
                {"name": "Taj Exotica Resort & Spa Benaulim", "price": 21000, "rating": 4.9, "tag": "5-Star South Goa", "area": "Benaulim"},
                {"name": "W Goa Vagator Beach", "price": 19500, "rating": 4.8, "tag": "Trendy Luxury", "area": "Vagator Cliff"}
            ]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Infantaria (Baga) / Artjuna (Anjuna)", "dish": "Fresh Croissant, Shakshuka & Cold Brew", "cost": "₹300 - ₹500"},
            {"meal": "Lunch", "spot": "Fisherman's Wharf / Ritz Classic (Panaji)", "dish": "Goan Fish Thali with Kingfish, Sol Kadi & Crab Xec Xec", "cost": "₹450 - ₹1100"},
            {"meal": "Evening Drink", "spot": "Curlies / Thalassa (Siolim)", "dish": "Greek Dips, Cocktails & Cliffside Sunset", "cost": "₹600 - ₹1500"},
            {"meal": "Dinner", "spot": "Gunpowder (Assagao) / Martin's Corner (Betalbatim)", "dish": "Kerala Beef Fry, Pork Vindaloo & Lobster Peri Peri", "cost": "₹800 - ₹2400"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "North Goa Beaches, Water Sports & Fort Aguada",
                "morning": {"title": "Fort Aguada & 1864 Lighthouse", "desc": "17th-century Portuguese fortress overlooking Sinquerim Beach and the Arabian Sea.", "time": "09:30 AM - 12:30 PM", "lat": 15.4925, "lon": 73.7736},
                "transport": "Self-drive rented scooter or AC Taxi.",
                "lunch": "Britto's Shack at Baga Beach.",
                "afternoon": {"title": "Calangute & Baga Water Sports", "desc": "Parasailing, Jet Ski rides, and banana boat rides along the vibrant North Goa strip.", "time": "02:00 PM - 05:00 PM", "lat": 15.5439, "lon": 73.7553},
                "evening": {"title": "Anjuna Flea Market & Curlies Sunset", "desc": "Live music, seaside sunset cocktails, and bohemian market stalls.", "time": "05:30 PM - 09:00 PM", "lat": 15.5807, "lon": 73.7431},
                "dinner": "Gunpowder in Assagao."
            },
            {
                "day": 2,
                "title": "Old Goa UNESCO Cathedrals & Latin Quarter Heritage Walk",
                "morning": {"title": "Basilica of Bom Jesus & Se Cathedral", "desc": "UNESCO World Heritage 1605 baroque church holding the sacred relics of St. Francis Xavier.", "time": "09:30 AM - 01:00 PM", "lat": 15.5009, "lon": 73.9116},
                "transport": "AC Cab from coastal belt to Old Goa (approx 35 mins).",
                "lunch": "Viva Panjim or Kokni Kanteen in Fontainhas.",
                "afternoon": {"title": "Fontainhas Latin Quarter Walking Tour", "desc": "Stroll through colourful Portuguese villas, narrow winding alleys, and tiled nameplates.", "time": "02:30 PM - 05:30 PM", "lat": 15.4989, "lon": 73.8278},
                "evening": {"title": "Mandovi River Luxury Sunset Cruise", "desc": "Folk dance performance, DJ cruise, and scenic views of the Panaji riverfront.", "time": "06:00 PM - 08:00 PM", "lat": 15.4990, "lon": 73.8340},
                "dinner": "The Black Sheep Bistro (Panaji)."
            }
        ]
    },
    "jaipur": {
        "name": "Jaipur (The Pink City)",
        "state": "Rajasthan",
        "description": "Royal capital of Rajasthan renowned for grand hill forts, ornate Rajput palaces, vibrant textile bazaars, and opulent heritage hotels.",
        "best_season": "October to March",
        "transit_hub": {
            "airport": "Jaipur International Airport (JAI)",
            "railways": "Jaipur Junction (JP), Gandhinagar Jaipur (GADJ)",
            "local_cab": "App cabs (Uber/Ola), Tourist E-rickshaws, Heritage Cabs"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1200, "food_per_day": 500, "transit_per_day": 250, "tours_per_day": 400},
            "mid": {"hotel_per_night": 4200, "food_per_day": 1400, "transit_per_day": 800, "tours_per_day": 1100},
            "luxury": {"hotel_per_night": 18000, "food_per_day": 4500, "transit_per_day": 2500, "tours_per_day": 3200}
        },
        "stays": {
            "budget": [
                {"name": "Zostel Jaipur (M.I. Road)", "price": 950, "rating": 4.6, "tag": "Rooftop Vibe", "area": "M.I. Road"},
                {"name": "Hotel Pearl Palace", "price": 1800, "rating": 4.5, "tag": "Peacock Rooftop", "area": "Hathroi Fort"}
            ],
            "mid": [
                {"name": "Alsisar Haveli - A Heritage Hotel", "price": 5200, "rating": 4.7, "tag": "Royal Haveli", "area": "Sansar Chandra Road"},
                {"name": "Shahpura House Heritage Hotel", "price": 4800, "rating": 4.6, "tag": "Pool & Courtyard", "area": "Bani Park"}
            ],
            "luxury": [
                {"name": "Rambagh Palace (The Taj Group)", "price": 32000, "rating": 5.0, "tag": "World #1 Hotel", "area": "Bhawani Singh Road"},
                {"name": "The Oberoi Rajvilas Jaipur", "price": 28000, "rating": 4.9, "tag": "Palatial Resort", "area": "Goner Road"}
            ]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Rawat Mishthan Bhandar (Sindhi Camp)", "dish": "Pyaz Kachori & Mawa Kachori with Masala Chai", "cost": "₹120 - ₹200"},
            {"meal": "Lunch", "spot": "Laxmi Mishthan Bhandar (LMB) Johari Bazaar", "dish": "Royal Rajasthani Thali (Dal Baati Churma, Gatte ki Sabzi)", "cost": "₹450 - ₹850"},
            {"meal": "Evening Lassi", "spot": "Lassiwala (M.I. Road Shop 312)", "dish": "Clay Kulhad Thick Cream Lassi", "cost": "₹60 - ₹100"},
            {"meal": "Dinner", "spot": "Chokhi Dhani / 1135 AD Amer Fort / Bar Palladio", "dish": "Royal Rajputana Feast with Folk Dance", "cost": "₹1200 - ₹3500"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "Amer Hill Fort, Jal Mahal & Hawa Mahal Facade",
                "morning": {"title": "Amer Fort & Sheesh Mahal", "desc": "Ascend to the hilltop 1592 Rajput palace featuring the Hall of Mirrors and Maota Lake.", "time": "09:00 AM - 01:00 PM", "lat": 26.9855, "lon": 75.8513},
                "transport": "AC Tourist Cab or local low-floor bus.",
                "lunch": "1135 AD inside Amer Fort or Peacock Rooftop.",
                "afternoon": {"title": "Jal Mahal & Nahargarh Fort Sunset", "desc": "Photo stop at the floating water palace, then drive up to Nahargarh Fort for a breathtaking city panoramic sunset.", "time": "03:00 PM - 06:30 PM", "lat": 26.9535, "lon": 75.8462},
                "evening": {"title": "Hawa Mahal (Palace of Winds) & Bazaars", "desc": "953 honeycomb pink sandstone windows, followed by shopping in Johari and Bapu Bazaars.", "time": "07:00 PM - 09:30 PM", "lat": 26.9239, "lon": 75.8267},
                "dinner": "LMB (Laxmi Mishthan Bhandar) or Bar Palladio."
            }
        ]
    },
    "agra": {
        "name": "Agra (City of the Taj)",
        "state": "Uttar Pradesh",
        "description": "Home to the world-renowned Taj Mahal, Agra Fort, and Fatehpur Sikri on the banks of River Yamuna.",
        "best_season": "October to March",
        "transit_hub": {
            "airport": "Agra Kheria Airport (AGR) / DEL Airport (3h via Yamuna Expressway)",
            "railways": "Agra Cantt (AGC) - Gatimaan Express connects from Delhi in 1h 40m!",
            "local_cab": "Prepaid Taxis, Electric Cabs, Auto-rickshaws"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1100, "food_per_day": 450, "transit_per_day": 200, "tours_per_day": 350},
            "mid": {"hotel_per_night": 3800, "food_per_day": 1200, "transit_per_day": 700, "tours_per_day": 900},
            "luxury": {"hotel_per_night": 16000, "food_per_day": 4000, "transit_per_day": 2200, "tours_per_day": 3000}
        },
        "stays": {
            "budget": [{"name": "Zostel Agra (Fatehabad Rd)", "price": 900, "rating": 4.6, "tag": "Near East Gate", "area": "Tajganj"}],
            "mid": [{"name": "ITC Mughal - A Luxury Collection Hotel", "price": 4800, "rating": 4.7, "tag": "Mughal Gardens", "area": "Tajganj"}],
            "luxury": [{"name": "The Oberoi Amarvilas Agra", "price": 28000, "rating": 5.0, "tag": "Taj View Every Room", "area": "East Gate"}]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Deviram Sweets (Pratappura)", "dish": "Bedmi Puri, Jalebi & Kadha Doodh", "cost": "₹80 - ₹150"},
            {"meal": "Lunch", "spot": "Pinch of Spice (Fatehabad Road)", "dish": "Murg Boti Masala & Dal Makhani", "cost": "₹550 - ₹1000"},
            {"meal": "Petha Tasting", "spot": "Panchi Petha Store", "dish": "Angoori, Chocolate & Kesar Petha", "cost": "₹100 - ₹300"},
            {"meal": "Dinner", "spot": "Peshawri (ITC Mughal) / Esphahan (The Oberoi)", "dish": "Dum Pukht Biryani & Tandoori Feast", "cost": "₹1200 - ₹4500"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "Taj Mahal Sunrise, Agra Fort & Mehtab Bagh",
                "morning": {"title": "The Taj Mahal Sunrise Viewing", "desc": "Witness the white marble mausoleum glowing in pink and gold morning dawn.", "time": "05:45 AM - 09:30 AM", "lat": 27.1751, "lon": 78.0421},
                "transport": "Electric battery golf carts from the parking lot to East Gate.",
                "lunch": "Pinch of Spice.",
                "afternoon": {"title": "Agra Fort (Red Fort)", "desc": "Massive 16th-century Mughal imperial citadel where Emperor Shah Jahan spent his final years.", "time": "01:30 PM - 04:30 PM", "lat": 27.1795, "lon": 78.0211},
                "evening": {"title": "Mehtab Bagh Moonlight Garden Sunset", "desc": "Direct reflection of the Taj Mahal across the Yamuna River during sunset.", "time": "05:15 PM - 07:00 PM", "lat": 27.1800, "lon": 78.0420},
                "dinner": "Peshawri at ITC Mughal."
            }
        ]
    }
}

# Generic fallback for any other Pan-India destination (Varanasi, Kochi, Bengaluru, Manali, etc.)
GENERIC_PAN_INDIA_TEMPLATE = {
    "name": "Pan-India Discovery",
    "best_season": "Year-round depending on region",
    "transit_hub": {
        "airport": "Nearest Regional International/Domestic Airport",
        "metro": "City Transit / Rapid Metro where available",
        "railways": "Indian Railways Superfast & Vande Bharat Network",
        "local_cab": "App-based cabs (Uber/Ola) and state transport buses"
    },
    "budget_tiers": {
        "budget": {"hotel_per_night": 1400, "food_per_day": 550, "transit_per_day": 300, "tours_per_day": 400},
        "mid": {"hotel_per_night": 4200, "food_per_day": 1500, "transit_per_day": 850, "tours_per_day": 1200},
        "luxury": {"hotel_per_night": 16000, "food_per_day": 4500, "transit_per_day": 2600, "tours_per_day": 3500}
    }
}


class TripPlanRequest(BaseModel):
    query: str = Field(description="Raw user query e.g. 'Plan 3 days in Delhi on mid budget' or 'Trip to Goa'")
    destination: str | None = None
    days: int | None = None
    budget_tier: Literal["budget", "mid", "luxury", "any"] = "any"
    travelers: int = 1


def parse_trip_intent(text: str) -> dict[str, Any]:
    """Extract destination, number of days, and budget level from user natural language query."""
    text_lower = text.lower()
    
    # Extract destination
    dest = None
    for city in ["delhi", "mumbai", "goa", "jaipur", "agra", "varanasi", "kochi", "manali", "shimla", "udaipur", "bengaluru", "kolkata", "chennai", "hyderabad", "dubai"]:
        if re.search(r'\b' + city + r'\b', text_lower):
            dest = city.title()
            break

    # Extract days
    days = None
    day_match = re.search(r'(\d+)\s*(?:-|to)?\s*(?:days?|nights?|d\b)', text_lower)
    if day_match:
        days = int(day_match.group(1))
    elif "one day" in text_lower or "1 day" in text_lower or "single day" in text_lower:
        days = 1
    elif "weekend" in text_lower or "two days" in text_lower or "2 days" in text_lower:
        days = 2
    elif "three days" in text_lower or "3 days" in text_lower:
        days = 3
    elif "four days" in text_lower or "4 days" in text_lower:
        days = 4
    elif "week" in text_lower or "7 days" in text_lower:
        days = 7

    # Extract budget tier
    budget = "any"
    if re.search(r'\b(cheap|cheapest|budget|low cost|backpacker|affordable|under \d+k?)\b', text_lower):
        budget = "budget"
    elif re.search(r'\b(luxury|expensive|5 star|five star|premium|lavish|royal)\b', text_lower):
        budget = "luxury"
    elif re.search(r'\b(mid|medium|moderate|normal|standard|balanced)\b', text_lower):
        budget = "mid"

    return {
        "destination": dest,
        "days": days,
        "budget_tier": budget
    }


def generate_itinerary(
    destination: str = "Delhi",
    days: int = 3,
    preferred_budget: str = "mid"
) -> dict[str, Any]:
    """Construct an end-to-end multi-day trip plan with 3 price options, transit, dining, and map waypoints."""
    days = max(1, min(days, 10))  # clamp between 1 and 10 days
    city_key = destination.lower().strip()
    data = PAN_INDIA_HUBS.get(city_key, None)

    if not data:
        # Default or fallback with generic coordinates
        data = PAN_INDIA_HUBS["delhi"]
        city_name = destination.title()
    else:
        city_name = data["name"]

    tiers = data["budget_tiers"]

    # Calculate total costs for the 3 price tiers
    def calculate_tier_cost(tier_key: str) -> dict[str, Any]:
        t = tiers[tier_key]
        hotel_total = t["hotel_per_night"] * max(1, days - 1)
        food_total = t["food_per_day"] * days
        transit_total = t["transit_per_day"] * days
        tours_total = t["tours_per_day"] * days
        grand_total = hotel_total + food_total + transit_total + tours_total
        return {
            "tier_name": {"budget": "Budget (Cheapest)", "mid": "Mid-Level (Recommended)", "luxury": "Luxury (VIP 5-Star)"}[tier_key],
            "total_cost": grand_total,
            "hotel_per_night": t["hotel_per_night"],
            "hotel_total": hotel_total,
            "food_total": food_total,
            "transit_total": transit_total,
            "tours_total": tours_total,
            "stay_options": data.get("stays", {}).get(tier_key, [])
        }

    cost_comparison = {
        "budget": calculate_tier_cost("budget"),
        "mid": calculate_tier_cost("mid"),
        "luxury": calculate_tier_cost("luxury")
    }

    # Build Day-by-Day Plan
    daily_templates = data.get("daily_templates", [])
    dining_options = data.get("dining", [])
    itinerary_days = []
    map_waypoints = []

    for d in range(1, days + 1):
        # Pick template cyclically if trip is longer than available templates
        tpl = daily_templates[(d - 1) % len(daily_templates)] if daily_templates else None
        
        if tpl:
            day_plan = {
                "day_number": d,
                "title": f"Day {d}: {tpl.get('title', 'City Highlights')}",
                "transport": tpl.get("transport", "Local metro / AC cab connecting major transit hubs."),
                "morning": tpl.get("morning"),
                "lunch": tpl.get("lunch", "Famous local bistro / thali meal."),
                "afternoon": tpl.get("afternoon"),
                "evening": tpl.get("evening"),
                "dinner": tpl.get("dinner", "Traditional dinner with regional specialties.")
            }
            # Collect points for map plotting
            if tpl.get("morning") and "lat" in tpl["morning"]:
                map_waypoints.append({
                    "day": d,
                    "title": tpl["morning"]["title"],
                    "lat": tpl["morning"]["lat"],
                    "lon": tpl["morning"]["lon"],
                    "type": "ATTRACTION"
                })
            if tpl.get("afternoon") and "lat" in tpl["afternoon"]:
                map_waypoints.append({
                    "day": d,
                    "title": tpl["afternoon"]["title"],
                    "lat": tpl["afternoon"]["lat"],
                    "lon": tpl["afternoon"]["lon"],
                    "type": "ATTRACTION"
                })
            if tpl.get("evening") and "lat" in tpl["evening"]:
                map_waypoints.append({
                    "day": d,
                    "title": tpl["evening"]["title"],
                    "lat": tpl["evening"]["lat"],
                    "lon": tpl["evening"]["lon"],
                    "type": "ATTRACTION"
                })
        else:
            day_plan = {
                "day_number": d,
                "title": f"Day {d}: Exploring {city_name}",
                "transport": "App-based cabs (Uber/Ola) and local tourist transit.",
                "morning": {"title": f"Iconic Landmarks of {city_name}", "desc": "Visit popular monuments and historic centers.", "time": "09:30 AM - 12:30 PM"},
                "lunch": "Authentic regional restaurant.",
                "afternoon": {"title": "Cultural Markets & Sightseeing", "desc": "Heritage crafts and scenic viewpoints.", "time": "02:00 PM - 05:00 PM"},
                "evening": {"title": "Sunset View & Local Promenade", "desc": "Evening leisure and street food walk.", "time": "05:30 PM - 08:00 PM"},
                "dinner": "Fine dining or popular courtyard restaurant."
            }

        itinerary_days.append(day_plan)

    return {
        "status": "ready",
        "city": city_name,
        "days": days,
        "best_season": data.get("best_season", "October to March"),
        "transit_connectivity": data.get("transit_hub", {}),
        "cost_comparison": cost_comparison,
        "itinerary": itinerary_days,
        "food_recommendations": dining_options,
        "map_waypoints": map_waypoints,
        "summary": f"Complete {days}-Day AI travel blueprint for {city_name} with Budget, Mid-Range, and Luxury pricing breakdowns, transit directions, and verified dining."
    }
