import pycurl
import urllib.parse
import io

# Function to perform sale transaction
def perform_sale(api_key, customer_data):
    query = ""

    # Login Information
    query += "security_key=" + urllib.parse.quote(api_key) + "&"
    
    # Sales Information
    query += "ccnumber=" + urllib.parse.quote(customer_data['ccnumber']) + "&"
    query += "ccexp=" + urllib.parse.quote(customer_data['ccexp']) + "&"
    query += "amount=" + urllib.parse.quote('{0:.2f}'.format(float(customer_data['amount']))) + "&"
    if 'cvv' in customer_data:
        query += "cvv=" + urllib.parse.quote(customer_data['cvv']) + "&"
    
    # Billing Information
    query += "firstname=" + urllib.parse.quote(customer_data['first_name']) + "&"
    query += "lastname=" + urllib.parse.quote(customer_data['last_name']) + "&"
    query += "address1=" + urllib.parse.quote(customer_data['address1']) + "&"
    query += "address2=" + urllib.parse.quote(customer_data['address2']) + "&"
    query += "city=" + urllib.parse.quote(customer_data['city']) + "&"
    query += "state=" + urllib.parse.quote(customer_data['state']) + "&"
    query += "zip=" + urllib.parse.quote(customer_data['zip']) + "&"
    
    # Additional fields
    query += "merchant_defined_field_1=" + urllib.parse.quote(customer_data.get('lead_id', '')) + "&"
    query += "merchant_defined_field_2=" + urllib.parse.quote(customer_data.get('lead_uid', '')) + "&"
    query += "customer_vault=" + urllib.parse.quote(customer_data.get('customer_vault', '')) + "&"
    
    # Set orderid same as lead_id
    query += "orderid=" + urllib.parse.quote(customer_data.get('lead_id', '')) + "&"
    
    query += "type=sale"

    return doPost(query)

# Function to perform HTTP POST request
def doPost(query):
    responseIO = io.BytesIO()
    curlObj = pycurl.Curl()
    curlObj.setopt(pycurl.POST, 1)
    curlObj.setopt(pycurl.CONNECTTIMEOUT, 30)
    curlObj.setopt(pycurl.TIMEOUT, 30)
    curlObj.setopt(pycurl.HEADER, 0)
    curlObj.setopt(pycurl.SSL_VERIFYPEER, 0)
    curlObj.setopt(pycurl.WRITEFUNCTION, responseIO.write)

    curlObj.setopt(pycurl.URL, "https://secure.tnbcigateway.com/api/transact.php")
    curlObj.setopt(pycurl.POSTFIELDS, query)

    curlObj.perform()

    data = responseIO.getvalue().decode('utf-8')
    temp = urllib.parse.parse_qs(data)
    responses = {}
    for key, value in temp.items():
        responses[key] = value[0]
    
    # Parse AVS Response
    avs_response = responses.get('avsresponse', '')
    avs_response_code = parse_avs_response(avs_response)
    responses['avs_response_code'] = avs_response_code
    
    # Parse CVV Response
    cvv_response = responses.get('cvvresponse', '')
    cvv_response_code = parse_cvv_response(cvv_response)
    responses['cvv_response_code'] = cvv_response_code
    
    # Parse Result Code
    result_code = responses.get('response_code', '')
    result_code_description = parse_result_code(result_code)
    responses['result_code_description'] = result_code_description
    
    return responses['response'], responses

# Function to parse AVS Response
def parse_avs_response(avs_response):
    avs_mapping = {
        "X": "Exact match, 9-character numeric ZIP",
        "Y": "Exact match, 5-character numeric ZIP",
        "D": "Exact match, 5-character numeric ZIP",
        "M": "Exact match, 5-character numeric ZIP",
        "2": "Exact match, 5-character numeric ZIP, customer name",
        "6": "Exact match, 5-character numeric ZIP, customer name",
        "A": "Address match only",
        "B": "Address match only",
        "3": "Address, customer name match only",
        "7": "Address, customer name match only",
        "W": "9-character numeric ZIP match only",
        "Z": "5-character ZIP match only",
        "P": "5-character ZIP match only",
        "L": "5-character ZIP match only",
        "1": "5-character ZIP, customer name match only",
        "5": "5-character ZIP, customer name match only",
        "N": "No address or ZIP match only",
        "C": "No address or ZIP match only",
        "4": "No address or ZIP or customer name match only",
        "8": "No address or ZIP or customer name match only",
        "U": "Address unavailable",
        "G": "Non-U.S. issuer does not participate",
        "I": "Non-U.S. issuer does not participate",
        "R": "Issuer system unavailable",
        "E": "Not a mail/phone order",
        "S": "Service not supported",
        "0": "AVS not available",
        "O": "AVS not available",
        "B": "AVS not available"
    }
    return avs_mapping.get(avs_response, "Unknown AVS Response")

# Function to parse CVV Response
def parse_cvv_response(cvv_response):
    cvv_mapping = {
        "M": "CVV2/CVC2 match",
        "N": "CVV2/CVC2 no match",
        "P": "Not processed",
        "S": "Merchant has indicated that CVV2/CVC2 is not present on card",
        "U": "Issuer is not certified and/or has not provided Visa encryption keys"
    }
    return cvv_mapping.get(cvv_response, "Unknown CVV Response")

# Function to parse Result Code
def parse_result_code(result_code):
    result_code_mapping = {
        "100": "Transaction was approved.",
        "200": "Transaction was declined by processor.",
        "201": "Do not honor.",
        "202": "Insufficient funds.",
        "203": "Over limit.",
        "204": "Transaction not allowed.",
        "220": "Incorrect payment information.",
        "221": "No such card issuer.",
        "222": "No card number on file with issuer.",
        "223": "Expired card.",
        "224": "Invalid expiration date.",
        "225": "Invalid card security code.",
        "226": "Invalid PIN.",
        "240": "Call issuer for further information.",
        "250": "Pick up card.",
        "251": "Lost card.",
        "252": "Stolen card.",
        "253": "Fraudulent card.",
        "260": "Declined with further instructions available. (See response text)",
        "261": "Declined-Stop all recurring payments.",
        "262": "Declined-Stop this recurring program.",
        "263": "Declined-Update cardholder data available.",
        "264": "Declined-Retry in a few days.",
        "300": "Transaction was rejected by gateway.",
        "400": "Transaction error returned by processor.",
        "410": "Invalid merchant configuration.",
        "411": "Merchant account is inactive.",
        "420": "Communication error.",
        "421": "Communication error with issuer.",
        "430": "Duplicate transaction at processor.",
        "440": "Processor format error.",
        "441": "Invalid transaction information.",
        "460": "Processor feature not available.",
        "461": "Unsupported card type."
    }
    return result_code_mapping.get(result_code, "Unknown Result Code")