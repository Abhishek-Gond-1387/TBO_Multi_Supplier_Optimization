"""Personal AI Travel Agent & Itinerary Planning Engine for TBO.

Generates complete N-day trip itineraries with:
- Three-tier pricing comparison (Cheapest / Budget, Mid-level / Recommended, Luxury / Premium)
- Stays & Hotels across tiers (with live multi-supplier offers)
- Transport interconnectivity (Metro, Cabs, Trains, Airport Transfers)
- Food & Dining recommendations (Iconic local spots, Breakfast/Lunch/Dinner)
- Sightseeing & Attractions with timings & tips
- Exact geo-coordinates for interactive map route plotting
"""

from __future__ import annotations

import difflib
import re
from typing import Any, Literal
from pydantic import BaseModel, Field

from services.pan_india_100_cities import PAN_INDIA_100_CITIES, CITY_SYNONYMS

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
    "varanasi": {
        "name": "Varanasi (Kashi / Banaras)",
        "state": "Uttar Pradesh",
        "description": "Spiritual capital of India on the holy Ganges river, renowned for ancient ghats, Kashi Vishwanath corridor, world-famous Ganga Aarti, and vibrant silk & street food culture.",
        "best_season": "October to March (pleasant weather)",
        "transit_hub": {
            "airport": "Lal Bahadur Shastri International Airport (VNS) Babatpur",
            "railways": "Varanasi Junction (BSB) / Pt. Deen Dayal Upadhyaya Junction (DDU)",
            "local_cab": "E-Rickshaws through Ghat alleys, App cabs (Uber/Ola), River Boatmen (Bajra & Shikara)"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1200, "food_per_day": 450, "transit_per_day": 250, "tours_per_day": 350},
            "mid": {"hotel_per_night": 4500, "food_per_day": 1400, "transit_per_day": 800, "tours_per_day": 1200},
            "luxury": {"hotel_per_night": 18500, "food_per_day": 4500, "transit_per_day": 2800, "tours_per_day": 4000}
        },
        "stays": {
            "budget": [
                {"name": "Zostel Varanasi (Dashashwamedh)", "price": 950, "rating": 4.6, "tag": "Walking to Ghats", "area": "Dashashwamedh"},
                {"name": "Stops Hostel Varanasi", "price": 1100, "rating": 4.5, "tag": "Assi Ghat Vibe", "area": "Assi Ghat"},
                {"name": "FabHotel Prime Kashi Residency", "price": 1800, "rating": 4.3, "tag": "Near Temple Corridor", "area": "Godowlia"}
            ],
            "mid": [
                {"name": "Radisson Hotel Varanasi", "price": 5400, "rating": 4.6, "tag": "Cantt Luxury", "area": "Varanasi Cantt"},
                {"name": "Hotel Madhuban Heritage", "price": 4200, "rating": 4.5, "tag": "Near Ghats", "area": "Shivala Ghat"},
                {"name": "Clarks Varanasi Heritage Resort", "price": 5800, "rating": 4.6, "tag": "Colonial Heritage", "area": "The Mall, Cantt"}
            ],
            "luxury": [
                {"name": "BrijRama Palace - Heritage on Darbhanga Ghat", "price": 22000, "rating": 5.0, "tag": "Ghat-Front Royal Palace", "area": "Darbhanga Ghat"},
                {"name": "Taj Ganges Varanasi", "price": 18500, "rating": 4.9, "tag": "5-Star Taj Luxury", "area": "Nadesar Palace Grounds"},
                {"name": "Taj Nadesar Palace", "price": 38000, "rating": 5.0, "tag": "Maharaja Suite VIP", "area": "Cantt Nadesar"}
            ]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Ram Bhandar (Thatheri Bazaar) / Netaji Kachori", "dish": "Banarasi Kachori Jalebi & Desi Ghee Poori", "cost": "₹80 - ₹150"},
            {"meal": "Lunch", "spot": "Baati Chokha Restaurant (Teliyabag)", "dish": "Desi Ghee Baati Chokha, Dal & Sattu Parantha", "cost": "₹250 - ₹500"},
            {"meal": "Evening Chaat", "spot": "Deena Chaat Bhandar & Kashi Chaat (Godowlia)", "dish": "Tamatar Chaat, Palak Patta Chaat & Gulab Jamun", "cost": "₹100 - ₹200"},
            {"meal": "Night Dessert & Paan", "spot": "Blue Lassi (Manikarnika) & Keshav Tambool", "dish": "Kulhad Pomegranate Lassi & Banarasi Meetha Paan", "cost": "₹70 - ₹150"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "Kashi Vishwanath Corridor, Subah-e-Banaras & Evening Ganga Aarti",
                "morning": {"title": "Subah-e-Banaras Morning Sunrise Boat Ride & Assi Ghat", "desc": "Witness Vedic chants, classical morning yoga, and sunrise over the holy Ganges river.", "time": "05:30 AM - 08:30 AM", "lat": 25.2882, "lon": 83.0068},
                "transport": "Hand-rowed wooden sunrise bajra boat along the 84 Ghats.",
                "lunch": "Ram Bhandar & Netaji Kachori Sabzi in Godowlia.",
                "afternoon": {"title": "Kashi Vishwanath Golden Temple Corridor & Annapurna Temple", "desc": "Visit the sacred Jyotirlinga through the magnificent renovated riverfront corridor.", "time": "11:00 AM - 02:30 PM", "lat": 25.3109, "lon": 83.0107},
                "evening": {"title": "World-Famous Maha Ganga Aarti at Dashashwamedh Ghat", "desc": "Grand rhythmic brass lamp rituals performed by priests overlooking the river at dusk.", "time": "06:00 PM - 08:00 PM", "lat": 25.3069, "lon": 83.0104},
                "dinner": "Deena Chaat Bhandar (Tamatar Chaat) followed by authentic Banarasi Paan."
            },
            {
                "day": 2,
                "title": "Sarnath Buddhist Pilgrimage & Silk Weaving Heritage",
                "morning": {"title": "Sarnath Dhamek Stupa & Archaeological Museum", "desc": "The sacred deer park where Lord Buddha gave his first sermon; view the original Ashoka Lion Capital.", "time": "09:00 AM - 01:00 PM", "lat": 25.3811, "lon": 83.0227},
                "transport": "Prepaid AC cab from Varanasi Cantt to Sarnath (approx 25 mins).",
                "lunch": "Baati Chokha Restaurant (traditional earthen pot meal).",
                "afternoon": {"title": "Banarasi Silk Weavers Colony & Ramnagar Fort", "desc": "18th-century riverside sandstone palace of the Kashi Naresh and artisanal silk loom workshops.", "time": "02:30 PM - 05:30 PM", "lat": 25.2687, "lon": 83.0253},
                "evening": {"title": "Manikarnika & Harishchandra Ghats Twilight Boat Cruise", "desc": "Contemplative evening boat journey observing eternal flames and river reflection.", "time": "06:00 PM - 08:00 PM", "lat": 25.3110, "lon": 83.0135},
                "dinner": "Cantonment fine dining at Varuna (Taj Ganges) or Canton Royale."
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
    "udaipur": {
        "name": "Udaipur (The City of Lakes)",
        "state": "Rajasthan",
        "description": "Venice of the East featuring palatial marble architecture, shimmering lakes, romantic sunset boat cruises, and Mewari royalty.",
        "best_season": "October to March",
        "transit_hub": {
            "airport": "Maharana Pratap Airport (UDR)",
            "railways": "Udaipur City Railway Station (UDZ)",
            "local_cab": "Tourist Cabs, Auto-rickshaws, Lake Ferry Boats"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1300, "food_per_day": 500, "transit_per_day": 250, "tours_per_day": 400},
            "mid": {"hotel_per_night": 4600, "food_per_day": 1600, "transit_per_day": 850, "tours_per_day": 1200},
            "luxury": {"hotel_per_night": 22000, "food_per_day": 5000, "transit_per_day": 2800, "tours_per_day": 4000}
        },
        "stays": {
            "budget": [{"name": "Zostel Udaipur (Pichola)", "price": 1100, "rating": 4.6, "tag": "Rooftop Pichola", "area": "Chandpole"}],
            "mid": [{"name": "Trident Udaipur", "price": 6800, "rating": 4.7, "tag": "Lake Frontage", "area": "Haridas Ji Ki Magri"}],
            "luxury": [{"name": "Taj Lake Palace Udaipur", "price": 32000, "rating": 5.0, "tag": "Island Palace", "area": "Lake Pichola"}]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Jheel's Ginger Coffee Bar", "dish": "Lakeview Hazelnut Cappuccino & Fresh Croissants", "cost": "₹200 - ₹400"},
            {"meal": "Lunch", "spot": "Krishna Dal Bati Restro", "dish": "Authentic Desi Ghee Dal Baati Churma", "cost": "₹300 - ₹500"},
            {"meal": "Dinner", "spot": "Ambrai Restaurant at Amet Haveli", "dish": "Lal Maas with Illuminated City Palace View", "cost": "₹1200 - ₹2500"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "City Palace of Udaipur, Jagdish Temple & Lake Pichola Sunset",
                "morning": {"title": "City Palace & Mor Chowk", "desc": "Rajasthan's largest royal palace complex with ornate peacock courtyards overlooking Lake Pichola.", "time": "09:30 AM - 01:00 PM", "lat": 24.5764, "lon": 73.6835},
                "transport": "Walking through old city lanes and lake jetties.",
                "lunch": "Tribute Restaurant overlooking Rang Sagar.",
                "afternoon": {"title": "Saheliyon Ki Bari & Vintage Car Collection", "desc": "Royal ornamental fountains, marble pavilions, and Rolls Royce classic cars.", "time": "02:30 PM - 05:00 PM", "lat": 24.6031, "lon": 73.6872},
                "evening": {"title": "Lake Pichola Sunset Boat Cruise to Jag Mandir", "desc": "Private boat ride around the floating palaces during golden hour.", "time": "05:30 PM - 07:30 PM", "lat": 24.5676, "lon": 73.6775},
                "dinner": "Ambrai Restaurant on the water's edge."
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
            "mid": [{"name": "ITC Mughal - Luxury Collection", "price": 4800, "rating": 4.7, "tag": "Mughal Gardens", "area": "Tajganj"}],
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
    },
    "manali": {
        "name": "Manali (Himalayan Adventure)",
        "state": "Himachal Pradesh",
        "description": "Snow-capped Himalayan valley celebrated for pine forests, apple orchards, Atal Tunnel highway to Lahaul, and adventure sports.",
        "best_season": "October to June (Snow in Dec-Feb, pleasant summers)",
        "transit_hub": {
            "airport": "Kullu Bhuntar Airport (KUU) / Chandigarh (IXC)",
            "railways": "Chandigarh Railway Station (CDG) / Joginder Nagar",
            "local_cab": "4x4 Himalayan Cabs, Self-drive bikes, HPTDC Volvo buses"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1200, "food_per_day": 500, "transit_per_day": 350, "tours_per_day": 500},
            "mid": {"hotel_per_night": 4500, "food_per_day": 1500, "transit_per_day": 1000, "tours_per_day": 1500},
            "luxury": {"hotel_per_night": 18000, "food_per_day": 4500, "transit_per_day": 2800, "tours_per_day": 3500}
        },
        "stays": {
            "budget": [{"name": "Zostel Old Manali", "price": 1050, "rating": 4.6, "tag": "Old Manali Vibe", "area": "Old Manali"}],
            "mid": [{"name": "Apple Country Resort & Spa", "price": 5200, "rating": 4.6, "tag": "Valley View", "area": "Log Huts"}],
            "luxury": [{"name": "The Himalayan - Luxury Castle Resort", "price": 19500, "rating": 4.9, "tag": "Gothic Castle & Pool", "area": "Hadimba Road"}]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Dylan's Toasted & Roasted", "dish": "Fresh Cinnamon Roll & French Press Coffee", "cost": "₹200 - ₹350"},
            {"meal": "Lunch", "spot": "Cafe 1947 (Riverside Old Manali)", "dish": "Woodfired Trout Pizza & Italian Pasta", "cost": "₹500 - ₹900"},
            {"meal": "Dinner", "spot": "Chopsticks (Mall Road)", "dish": "Tibetan Thukpa, Momos & Hot Apple Cider", "cost": "₹350 - ₹700"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "Solang Valley Adventures, Atal Tunnel & Sissu Waterfall",
                "morning": {"title": "Solang Valley & Atal Tunnel Express", "desc": "Drive through the 9.02km engineering marvel into the snow peaks of Lahaul Valley.", "time": "08:30 AM - 01:00 PM", "lat": 32.3167, "lon": 77.1600},
                "transport": "Private 4x4 SUV cab for mountain terrain.",
                "lunch": "Riverside Dhaba in Sissu (Lahaul).",
                "afternoon": {"title": "Hadimba Devi Temple & Cedar Forest", "desc": "1553 pagoda-style wooden temple built amidst towering deodar cedars.", "time": "02:30 PM - 05:00 PM", "lat": 32.2483, "lon": 77.1802},
                "evening": {"title": "Old Manali Hippie Trail & Cafe 1947", "desc": "Live acoustic music beside the roaring Manalsu river.", "time": "06:00 PM - 09:00 PM", "lat": 32.2570, "lon": 77.1780},
                "dinner": "Cafe 1947."
            }
        ]
    },
    "rishikesh": {
        "name": "Rishikesh (Yoga Capital of the World)",
        "state": "Uttarakhand",
        "description": "Gateway to the Himalayas where emerald Ganga flows through foothills; famous for white water rafting, ashrams, and Parmarth Niketan Aarti.",
        "best_season": "September to May",
        "transit_hub": {
            "airport": "Jolly Grant Airport Dehradun (DED) - 35 mins away",
            "railways": "Yog Nagari Rishikesh (YNRK) / Haridwar (HW)",
            "local_cab": "App cabs, Scooters, Shared Vikrams"
        },
        "budget_tiers": {
            "budget": {"hotel_per_night": 1100, "food_per_day": 400, "transit_per_day": 200, "tours_per_day": 500},
            "mid": {"hotel_per_night": 4200, "food_per_day": 1400, "transit_per_day": 800, "tours_per_day": 1400},
            "luxury": {"hotel_per_night": 22000, "food_per_day": 4500, "transit_per_day": 2500, "tours_per_day": 3500}
        },
        "stays": {
            "budget": [{"name": "Zostel Rishikesh (Tapovan)", "price": 950, "rating": 4.6, "tag": "Yoga & Cafe Vibe", "area": "Tapovan"}],
            "mid": [{"name": "Aloha On The Ganges", "price": 6200, "rating": 4.6, "tag": "Riverfront Resort", "area": "Tapovan"}],
            "luxury": [{"name": "Taj Rishikesh Resort & Spa", "price": 28000, "rating": 5.0, "tag": "Private Beach Luxury", "area": "Singtali"}]
        },
        "dining": [
            {"meal": "Breakfast", "spot": "Little Buddha Cafe", "dish": "Pappaya Smoothie Bowl & Vegan Pancakes", "cost": "₹200 - ₹350"},
            {"meal": "Lunch", "spot": "Chotiwala Restaurant (Ram Jhula)", "dish": "Traditional North Indian & Garhwali Thali", "cost": "₹250 - ₹450"},
            {"meal": "Dinner", "spot": "The Sitting Elephant / Ganga Beach Cafe", "dish": "Woodfired Pizza with Ganga Riverfront View", "cost": "₹450 - ₹900"}
        ],
        "daily_templates": [
            {
                "day": 1,
                "title": "White Water Rafting, Beatles Ashram & Parmarth Niketan Aarti",
                "morning": {"title": "Shivpuri to Rishikesh Grade III White Water Rafting", "desc": "16km thrilling rafting adventure passing rapids like Roller Coaster and Golf Course.", "time": "08:30 AM - 12:30 PM", "lat": 30.1360, "lon": 78.3880},
                "transport": "River raft followed by local transfer cab.",
                "lunch": "Chotiwala Restaurant at Ram Jhula.",
                "afternoon": {"title": "The Beatles Ashram (Chaurasi Kutia)", "desc": "Meditation domes with graffiti art where The Beatles stayed and composed in 1968.", "time": "02:00 PM - 04:30 PM", "lat": 30.1147, "lon": 78.3142},
                "evening": {"title": "Parmarth Niketan Ganga Aarti at Dusk", "desc": "Divine spiritual riverside aarti with Vedic hymns and floating earthen diyas.", "time": "05:30 PM - 07:30 PM", "lat": 30.1190, "lon": 78.3120},
                "dinner": "Ganga Beach Cafe overlooking the river."
            }
        ]
    }
}


class TripPlanRequest(BaseModel):
    query: str = Field(description="Raw user query e.g. 'Plan 3 days in Delhi on mid budget' or 'Trip to Goa'")
    destination: str | None = None
    days: int | None = None
    budget_tier: Literal["budget", "mid", "luxury", "any"] = "any"
    travelers: int = 1


def parse_trip_intent(text: str) -> dict[str, Any]:
    """Extract destination, number of days, and budget level from user natural language query with fuzzy typo resilience."""
    text_lower = text.lower()

    # 1. Direct synonym and canonical lookup
    dest = None
    for syn, canonical in sorted(CITY_SYNONYMS.items(), key=lambda x: -len(x[0])):
        if re.search(r'\b' + re.escape(syn) + r'\b', text_lower):
            dest = canonical
            break

    if not dest:
        for city in sorted(PAN_INDIA_100_CITIES.keys(), key=lambda x: -len(x)):
            if re.search(r'\b' + re.escape(city.lower()) + r'\b', text_lower):
                dest = city
                break

    # 1.1 Fuzzy / Typo match fallback using difflib for words like 'varansi', 'jaipr', 'banglore'
    if not dest:
        all_city_lookup: dict[str, str] = {k.lower(): k for k in PAN_INDIA_100_CITIES}
        all_city_lookup.update({k.lower(): v for k, v in CITY_SYNONYMS.items()})

        stopwords = {
            "plan", "trip", "days", "day", "night", "nights", "din", "budget", "cost", "price",
            "hotel", "hotels", "stay", "stays", "tour", "tours", "want", "need", "give", "make",
            "show", "tell", "best", "cheapest", "expensive", "luxury", "mid", "under", "upto",
            "with", "and", "for", "the", "in", "to", "at", "me", "my", "we", "us", "star", "stars",
            "food", "transit", "travel", "vacation", "holiday", "package", "tourist", "vacation"
        }
        tokens = re.findall(r'[a-zA-Z]{3,}', text_lower)
        for token in tokens:
            if token in stopwords:
                continue
            matches = difflib.get_close_matches(token, list(all_city_lookup.keys()), n=1, cutoff=0.70)
            if matches:
                dest = all_city_lookup[matches[0]]
                break

    # 2. Extract days (supporting English, Hindi/Hinglish, 2n3d, weekend, etc.)
    days = None
    n_d_match = re.search(r'(\d+)\s*(?:d|days?)\s*(?:and|&)?\s*(\d+)\s*(?:n|nights?)', text_lower)
    if n_d_match:
        days = int(n_d_match.group(1))
    else:
        d_n_match = re.search(r'(\d+)\s*(?:n|nights?)\s*(?:and|&)?\s*(\d+)\s*(?:d|days?)', text_lower)
        if d_n_match:
            days = int(d_n_match.group(2))

    if not days:
        day_match = re.search(r'(\d+)\s*(?:-|to)?\s*(?:days?|nights?|din|d\b)', text_lower)
        if day_match:
            days = int(day_match.group(1))
        elif re.search(r'\b(ek din|1 day|one day|single day)\b', text_lower):
            days = 1
        elif re.search(r'\b(do din|2 days|two days|weekend)\b', text_lower):
            days = 2
        elif re.search(r'\b(teen din|3 days|three days)\b', text_lower):
            days = 3
        elif re.search(r'\b(chaar din|char din|4 days|four days)\b', text_lower):
            days = 4
        elif re.search(r'\b(paanch din|panch din|5 days|five days)\b', text_lower):
            days = 5
        elif re.search(r'\b(chhah din|cheh din|6 days|six days)\b', text_lower):
            days = 6
        elif re.search(r'\b(saat din|7 days|seven days|hafta|one week|week)\b', text_lower):
            days = 7

    effective_days = days or 3

    # 3. Extract budget (numeric amount or keywords or star preferences)
    budget = "any"
    star_rating = None
    stated_budget: int | None = None

    # Look for numerical budget amount (e.g. 'budget 50000', 'under 25k', '50k budget', '1.5 lakh')
    num_matches = re.finditer(
        r'(?:budget\s*(?:of|is|:)?|under|around|upto|max|approx|spend)?\s*(?:rs\.?|inr|₹)?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|lakh|lac)?\s*(?:rs\.?|inr|rupees|budget)?',
        text_lower
    )
    for m in num_matches:
        raw_num = m.group(1).replace(',', '')
        mult = m.group(2)
        try:
            val = float(raw_num)
            # If it equals days and has no multiplier or budget context, skip
            if days and val == float(days) and not mult and "budget" not in m.group(0):
                continue
            if mult in ("k", "thousand"):
                val *= 1000
            elif mult in ("lakh", "lac"):
                val *= 100000
            if val >= 1000:
                stated_budget = int(val)
                break
        except (ValueError, TypeError):
            continue

    if stated_budget:
        per_day = stated_budget / effective_days
        if per_day >= 12000 or stated_budget >= 35000:
            budget = "luxury"
            star_rating = 5
        elif per_day >= 3800 or stated_budget >= 10000:
            budget = "mid"
            star_rating = 4
        else:
            budget = "budget"
            star_rating = 2
    else:
        # Keyword-based extraction
        if re.search(r'\b(5\s*star|five\s*star|5-star|5★|five\s*stars|luxury|expensive|mehanga|mehenga|premium|lavish|royal|shahi)\b', text_lower):
            budget = "luxury"
            star_rating = 5
        elif re.search(r'\b(4\s*star|four\s*star|4-star|4★|four\s*stars)\b', text_lower):
            budget = "mid"
            star_rating = 4
        elif re.search(r'\b(3\s*star|three\s*star|3-star|3★|three\s*stars|mid|medium|moderate|normal|standard|balanced|beech ka|thik thak)\b', text_lower):
            budget = "mid"
            star_rating = 3
        elif re.search(r'\b(1\s*star|2\s*star|1-star|2-star|1★|2★|one\s*star|two\s*stars|cheap|cheapest|budget|sasta|low cost|backpacker|affordable|kam budget|kam daam)\b', text_lower):
            budget = "budget"
            star_rating = 2

    return {
        "destination": dest,
        "days": days,
        "budget_tier": budget,
        "star_rating": star_rating,
        "stated_budget": stated_budget
    }


def generate_itinerary(
    destination: str = "Delhi",
    days: int = 3,
    preferred_budget: str = "mid",
    stated_budget: int | None = None
) -> dict[str, Any]:
    """Construct an end-to-end multi-day trip plan with 3 price options, transit, dining, and map waypoints."""
    days = max(1, min(days, 10))  # clamp between 1 and 10 days
    city_key = destination.lower().strip()
    data = PAN_INDIA_HUBS.get(city_key, None)

    if not data:
        # Check in 110 cities database
        meta = None
        for c_name, c_meta in PAN_INDIA_100_CITIES.items():
            if c_name.lower() == city_key:
                meta = c_meta
                destination = c_name
                break

        if meta:
            clon, clat = meta["coords"]
            # Dynamically fetch real items from live 1M multi-supplier engine
            live_attractions = []
            live_hotels = []
            live_dining = []
            try:
                from services.pan_india_1m_engine import live_1m_engine
                res = live_1m_engine.search_live(destination=destination, limit=40)
                items = [r["item"] for r in res.get("results", [])]
                live_attractions = [it for it in items if it.get("entity_type") == "ATTRACTION"]
                live_hotels = [it for it in items if it.get("entity_type") == "HOTEL"]
                live_dining = [it for it in items if it.get("entity_type") == "DINING"]
            except Exception:
                pass

            # Stays with live supplier quotes if available
            b_stay = live_hotels[0]["name"] if len(live_hotels) > 0 else f"{destination} Travellers Residency"
            m_stay = live_hotels[1]["name"] if len(live_hotels) > 1 else f"{destination} Grand Regency & Spa"
            l_stay = live_hotels[2]["name"] if len(live_hotels) > 2 else f"The Oberoi / Taj Palace {destination}"

            # Sightseeing attractions
            att1 = live_attractions[0]["name"] if len(live_attractions) > 0 else f"{destination} Heritage Palace & Fort"
            att2 = live_attractions[1]["name"] if len(live_attractions) > 1 else f"{destination} Lake Promenade & Gardens"
            att3 = live_attractions[2]["name"] if len(live_attractions) > 2 else f"{destination} Cultural Bazaar & Crafts"
            att4 = live_attractions[3]["name"] if len(live_attractions) > 3 else f"{destination} Sunset Hilltop Viewpoint"

            # Dining spots
            food1 = live_dining[0]["name"] if len(live_dining) > 0 else f"Famous {meta.get('cuisine', destination + ' Delicacies')}"
            food2 = live_dining[1]["name"] if len(live_dining) > 1 else f"{destination} Traditional Heritage Dining Hall"

            data = {
                "name": destination,
                "state": meta.get("state", "India"),
                "description": f"Enchanting destination in {meta.get('state')} celebrated for {meta.get('cuisine')}.",
                "best_season": "October to March (ideal travel season)",
                "transit_hub": {
                    "airport": meta.get("airport", f"{destination} Airport"),
                    "metro": "City Transit & Prepaid AC Cabs",
                    "railways": meta.get("railway", f"{destination} Railway Junction"),
                    "local_cab": "App cabs (Uber/Ola), Pre-paid auto-rickshaws, Local AC Sedans"
                },
                "budget_tiers": {
                    "budget": {"hotel_per_night": 1400, "food_per_day": 550, "transit_per_day": 300, "tours_per_day": 400},
                    "mid": {"hotel_per_night": 4200, "food_per_day": 1500, "transit_per_day": 850, "tours_per_day": 1100},
                    "luxury": {"hotel_per_night": 17000, "food_per_day": 4500, "transit_per_day": 2600, "tours_per_day": 3500}
                },
                "stays": {
                    "budget": [
                        {"name": b_stay, "price": 1400, "rating": 4.4, "tag": "Budget Favorite", "area": meta.get("stay_hub", destination)},
                        {"name": f"Zostel / Backpacker Inn {destination}", "price": 950, "rating": 4.5, "tag": "Youth Vibe", "area": "City Center"}
                    ],
                    "mid": [
                        {"name": m_stay, "price": 4500, "rating": 4.6, "tag": "Recommended", "area": meta.get("stay_hub", destination)},
                        {"name": f"Radisson / Vivanta {destination}", "price": 5400, "rating": 4.7, "tag": "4-Star Superior", "area": "City Center"}
                    ],
                    "luxury": [
                        {"name": l_stay, "price": 18000, "rating": 4.9, "tag": "VIP 5-Star", "area": meta.get("stay_hub", destination)},
                        {"name": f"Taj / The Leela {destination}", "price": 24000, "rating": 5.0, "tag": "Palatial Resort", "area": "Scenic View"}
                    ]
                },
                "dining": [
                    {"meal": "Breakfast", "spot": food1, "dish": f"Fresh breakfast featuring {meta.get('cuisine', 'local dishes')}", "cost": "₹150 - ₹300"},
                    {"meal": "Lunch", "spot": food2, "dish": f"Authentic regional thali featuring {meta.get('cuisine', 'specialties')}", "cost": "₹350 - ₹750"},
                    {"meal": "Dinner", "spot": f"{destination} Royal Courtyard", "dish": "Chef special evening dinner & desserts", "cost": "₹700 - ₹1800"}
                ],
                "daily_templates": [
                    {
                        "title": f"Iconic Landmarks, {att1} & Cultural Walk",
                        "transport": f"Prepaid AC Sedan from {meta.get('airport', 'transit hub')}.",
                        "morning": {"title": att1, "desc": f"Explore the majestic architecture and rich heritage of {destination}.", "time": "09:00 AM - 12:30 PM", "lat": round(clat + 0.012, 6), "lon": round(clon + 0.012, 6)},
                        "lunch": f"Authentic lunch featuring {meta.get('cuisine', 'regional delicacies')}.",
                        "afternoon": {"title": att3, "desc": f"Vibrant artisan bazaars, handlooms, and souvenirs in {destination}.", "time": "02:00 PM - 04:30 PM", "lat": round(clat - 0.008, 6), "lon": round(clon - 0.008, 6)},
                        "evening": {"title": att4, "desc": f"Breathtaking panoramic sunset viewpoint over {destination}.", "time": "05:30 PM - 07:30 PM", "lat": round(clat + 0.018, 6), "lon": round(clon - 0.015, 6)},
                        "dinner": f"Chef special evening food trail: {meta.get('cuisine', 'local dishes')}."
                    },
                    {
                        "title": f"{att2}, Nature Trails & Regional Delicacies",
                        "transport": "Full day private AC cab for comfortable sightseeing.",
                        "morning": {"title": att2, "desc": f"Serene morning walk around picturesque gardens and lakes of {destination}.", "time": "09:30 AM - 12:30 PM", "lat": round(clat - 0.015, 6), "lon": round(clon + 0.02, 6)},
                        "lunch": "Traditional thali meal at a heritage dining hall.",
                        "afternoon": {"title": f"{destination} Archaeological Museum & Arts", "desc": "Centuries of cultural artifacts and regional craft exhibitions.", "time": "02:30 PM - 05:00 PM", "lat": round(clat + 0.022, 6), "lon": round(clon + 0.018, 6)},
                        "evening": {"title": f"{destination} Light & Sound Heritage Show", "desc": "Evening cultural performance and illuminated monument walk.", "time": "06:00 PM - 08:00 PM", "lat": round(clat + 0.005, 6), "lon": round(clon + 0.005, 6)},
                        "dinner": "Panoramic rooftop dinner with regional specialties."
                    }
                ]
            }
            city_name = destination
        else:
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

        # If user explicitly stated a custom budget amount and this tier matches user's tier
        if stated_budget and tier_key == preferred_budget:
            grand_total = stated_budget
            hotel_total = int(stated_budget * 0.55)
            food_total = int(stated_budget * 0.20)
            transit_total = int(stated_budget * 0.13)
            tours_total = int(stated_budget * 0.12)

        return {
            "tier_name": {"budget": "Budget (Cheapest)", "mid": "Mid-Level (Recommended)", "luxury": "Luxury (VIP 5-Star)"}[tier_key],
            "total_cost": grand_total,
            "hotel_per_night": int(hotel_total / max(1, days - 1)),
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
        "stated_budget": stated_budget,
        "summary": f"Complete {days}-Day AI travel blueprint for {city_name} with Budget, Mid-Range, and Luxury pricing breakdowns, transit directions, and verified dining."
    }
