from flask import Flask, jsonify, request
import pandas as pd
import re, os, requests

app = Flask(__name__)

# constants
FMCSA_KEY = 'cdc33e44d693a3a58451898d4ec9df862c65b954'

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

## BEGIN: loading datasets ##
# load csv 
file_path = 'carrier_loads.csv'
df = pd.read_csv(file_path)

# # load carrier information for mc number verification
# mc_response = requests.get(f"https://mobile.fmcsa.dot.gov/qc/services/carriers/name/greyhound?webKey={FMCSA_KEY}")
# mc_data = mc_response.json()
# # mc_df = pd.DataFrame(mc_data['content'])
# mc_df = pd.json_normalize(mc_data['content'])
# print(mc_df.info())
# print(type(mc_df['carrier.allowedToOperate']))

## END: loading datasets ##

# function to process reference number-- AI sometimes does not process the user saying 'R E F'
def process_ref_num(reference_number):
    numbers =  ''.join(re.findall(r'\d+', reference_number))
    return 'REF' + numbers

# function to process mc number-- AI sometimes does not process the user saying 'M C'
def process_mc_num(mc_number):
    numbers =  ''.join(re.findall(r'\d+', mc_number))
    return 'MC' + numbers

# function to search csv file
def search_loads_by_ref_num(reference_number):
    """Search for a row in the load information dataframe by reference number."""
    row = df[df['reference_number'] == reference_number]
    if not row.empty:
        return row.to_dict(orient="records")[0] 
    return None

def search_loads_by_lane_and_trailer(lane, trailer):
    """Search for a row in the load information dataframe by lane and trailer."""
    origin, destination = process_lane(lane)
    trailer = process_trailer(trailer)
    row = df[(df['origin'] == origin) & (df['destination'] == destination) & (df['equipment_type'].str.contains(trailer))]
    if not row.empty:
        return row.to_dict(orient="records")[0] 
    return None

def process_lane(lane):
    """Denver, Colorado to Detroit, Michigan"""
    print(f"Type of lane immediaely after calling process lane: {type(lane)}")

    if not isinstance(lane, str):
        raise ValueError(f"Expected a string input for 'lane' {type(lane)}")
    
    pattern = r'\b\w+,\s\w+\b'
    matches = re.findall(pattern, lane)
    locations = []
    for location in matches:
        city, state = location.split(',')
        state = state.strip()
        if len(state) > 2:
            state = STATE_ABBREV[state]
        city_state_str = city + ', ' + state
        locations.append(city_state_str)

    return locations[0], locations[1]

def process_trailer(trailer):
    trailer_list = trailer.split()
    capitalized_trailer = ""
    for item in trailer_list:
        capitalized_item = item.capitalize()
        if len(capitalized_trailer) > 0:
            capitalized_trailer += " "  
        capitalized_trailer += capitalized_item
    return capitalized_trailer



@app.route('/', methods=['GET'])
def home():
    return "hello world"

@app.route('/loads', methods=['GET', 'POST'])
# GET reference number
def find_available_loads():
    params = request.args
    has_ref_num = 'reference_number' in params
    has_lane_and_trailer = ('lane' in params) and ('trailer' in params)
    if not(has_ref_num) and not(has_lane_and_trailer):
        return jsonify({"error": "reference_number or lane and trailer parameter is required"}), 400
    if has_ref_num: 
        reference_number = request.args.get('reference_number')
        reference_number = process_ref_num(reference_number)
        try: 
            result = search_loads_by_ref_num(reference_number)
            if result:
                return jsonify(result), 200
            else:
                return jsonify({"error" : "Reference number not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    elif has_lane_and_trailer:
        lane = request.args.get('lane')
        # raise ValueError(f"Lane {type(lane)}")
        # lane = process_lane(lane)
        trailer = request.args.get('trailer')

        try: 
            print(f"Type of lane immediaely befire calling process lane: {type(lane)}")
            result = search_loads_by_lane_and_trailer(lane, trailer)
            if result:
                return jsonify(result), 200
            else:
                return jsonify({"error" : "Lane and trailer not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    

@app.route('/carrier', methods=['GET'])
# GET mc number from carrier
def verify_carrier():
    mc_number = request.args.get('mc_number')
    if not(mc_number):
        return jsonify({"error": "mc_number parameter is required"}), 400
    print("mc_number from verify_carrier(): ", mc_number)

    try:
        # mc_number = process_mc_num(mc_number)
        # print(mc_number)
        # url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/{mc_number}?webKey={FMCSA_KEY}"
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
            return jsonify({"error" : "Issue getting response"}), 404
    
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))

# necessary APIs: GET reference number, GET mc number
