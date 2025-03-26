from flask import Flask, jsonify
import pandas as pd
import re, os

app = Flask(__name__)

# load csv 
file_path = 'carrier_loads.csv'
df = pd.read_csv(file_path)

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

## API ##

@app.route('/', methods=['GET'])
def home():
    return "hello world"

@app.route('/loads/<string:reference_number>', methods=['GET'])
# GET reference number
def find_available_loads(reference_number):
    result = search_loads(reference_number)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error" : "Reference number not found"}), 404

@app.route('/carrier/<string:mc_number>', methods=['GET'])
# GET mc number
def verify_carrier(mc_number):
    # use the key
    pass




if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# necessary APIs: GET reference number, GET mc number
