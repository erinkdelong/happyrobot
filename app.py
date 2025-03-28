from flask import Flask, jsonify, request
import pandas as pd
import re, os, requests
from functools import wraps
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

#####
# Constants
FMCSA_KEY = os.getenv("FMCSA_KEY")
API_KEY = os.getenv("API_KEY")



# Mapping of full state names to abbreviations
STATE_ABBREV = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY'
}

# Path to the CSV file containing load information and load information dataframe
LOADS_FILE_PATH = 'carrier_loads.csv'
LOADS_INFO_DF = pd.read_csv(LOADS_FILE_PATH)

#####

# Function to process reference number and handle string variations (e.g., 'R E F' vs 'REF')
def process_ref_num(reference_number):
    numbers =  ''.join(re.findall(r'\d+', reference_number))
    return 'REF' + numbers

# Function to process MC number and handle variations (e.g., 'M C' vs 'MC')
def process_mc_num(mc_number):
    numbers =  ''.join(re.findall(r'\d+', mc_number))
    return 'MC' + numbers

# Function to search loads by reference number
def search_loads_by_ref_num(reference_number):
    """Search for a row in the load information dataframe by reference number."""
    row = LOADS_INFO_DF[LOADS_INFO_DF['reference_number'] == reference_number]
    if not row.empty:
        return row.to_dict(orient="records")[0] 
    return None

# Function to search loads by lane and trailer type
def search_loads_by_lane_and_trailer(lane, trailer):
    """Search for a row in the load information dataframe by lane and trailer."""
    origin, destination = process_lane(lane)
    trailer = process_trailer(trailer)
    row = LOADS_INFO_DF[(LOADS_INFO_DF['origin'] == origin) & (LOADS_INFO_DF['destination'] == destination) & (LOADS_INFO_DF['equipment_type'].str.contains(trailer))]
    if not row.empty:
        return row.to_dict(orient="records")[0] 
    return None

# Function to process the lane input, extracting city and state
def process_lane(lane):
    """Denver, Colorado to Detroit, Michigan"""

    pattern = r'\b\w+,\s\w+\b'
    lowercase_lane = lane.lower()
    matches = re.findall(pattern, lowercase_lane)
    locations = []
    for location in matches:
        city, state = location.split(',')
        city = city.strip()
        city = city.capitalize()
        state = state.strip()
        state = state.capitalize()
        if len(state) > 2:
            state = STATE_ABBREV[state]
        else:
            state =  state.upper()
        city_state_str = city + ', ' + state
        locations.append(city_state_str)

    return locations[0], locations[1]

# Function to process the trailer type, ensuring proper case formatting
def process_trailer(trailer):
    lowercase_trailer = trailer.lower()
    trailer_list = lowercase_trailer.split()
    capitalized_trailer = ""
    for item in trailer_list:
        capitalized_item = item.capitalize()
        if len(capitalized_trailer) > 0:
            capitalized_trailer += " "  
        capitalized_trailer += capitalized_item
    return capitalized_trailer


# Retrieve API key
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-HR-KEY')
        if api_key == None or API_KEY == None:
            return jsonify({"error": "Key is None"}), 401
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Route for the home page
@app.route('/', methods=['GET'])
def home():
    return "Welcome to Erin's HappyRobot Trucking Project"

# Route to find available loads based on reference number or lane and trailer
@app.route('/loads', methods=['GET'])
@require_api_key
def find_available_loads():
    params = request.args
    has_ref_num = 'reference_number' in params
    has_lane_and_trailer = ('lane' in params) and ('trailer' in params)
    if not(has_ref_num) and not(has_lane_and_trailer):
        return jsonify({"error": "reference_number or lane and trailer parameter is required"}), 400
    
    try:
        if has_ref_num: 
            reference_number = request.args.get('reference_number')
            reference_number = process_ref_num(reference_number)
            result = search_loads_by_ref_num(reference_number)
            if result:
                return jsonify(result), 200
            else:
                return jsonify({"error" : "Reference number not found"}), 404

        elif has_lane_and_trailer:
            lane = request.args.get('lane')
            # raise ValueError(f"Lane {type(lane)}")
            # lane = process_lane(lane)
            trailer = request.args.get('trailer')
            result = search_loads_by_lane_and_trailer(lane, trailer)
            if result:
                return jsonify(result), 200
            else:
                return jsonify({"error" : "Lane and trailer not found"}), 404
            
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

# Route to verify a carrier using its MC number
@app.route('/carrier', methods=['GET'])
@require_api_key
def verify_carrier():
    mc_number = request.args.get('mc_number')
    if not(mc_number):
        return jsonify({"error": "mc_number parameter is required"}), 400

    try:
        url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{mc_number}?webKey={FMCSA_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            isAllowedToOperate = data['content'][0]['carrier']['allowedToOperate']
            if isAllowedToOperate:
                legal_name = data["content"][0]["carrier"]["legalName"]
                return jsonify({'verified': True, "legal_name": legal_name}), 200
            else:
                return jsonify({"verified" : False}), 200
        else:
            return jsonify({"error" : f"Issue getting response from FMCSA API: {response.status_code}"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    
# Run Flask app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))

