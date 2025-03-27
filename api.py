from flask import Flask, jsonify
import pandas as pd
import re, os, requests

app = Flask(__name__)

# keys
FMCSA_KEY = 'cdc33e44d693a3a58451898d4ec9df862c65b954'

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
def search_loads(reference_number):
    """Search for a row in the load information dataframe by reference number."""
    row = df[df['reference_number'] == reference_number]
    if not row.empty:
        return row.to_dict(orient="records")[0] 
    return None


@app.route('/', methods=['GET'])
def home():
    return "hello world"

@app.route('/loads/<string:reference_number>', methods=['GET'])
# GET reference number
def find_available_loads(reference_number):
    try: 
        reference_number = process_ref_num(reference_number)
        result = search_loads(reference_number)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({"error" : "Reference number not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/carrier/<string:mc_number>', methods=['GET'])
# GET mc number from carrier
def verify_carrier(mc_number):
    try:
        # mc_number = process_mc_num(mc_number)
        # print(mc_number)
        url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/{mc_number}?webKey={FMCSA_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            isAllowedToOperate = data['content']['carrier']['allowedToOperate']
            return jsonify({"allowedToOperate": isAllowedToOperate}), 200
        else:
            return jsonify({"error" : "mc number not found"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))

# necessary APIs: GET reference number, GET mc number
