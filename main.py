import pyodbc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import logging
import uvicorn
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from payment import perform_sale
from models import (
    Step2Response,
    Step1Request,
    Step1Response,
    Step2Request,
    Step3Request,
    Step4Request,
    Step4Response,
    EmailSchema,
    RemoveDataRequest,
)
from typing import List, Optional

app = FastAPI()

API_KEY = "xtYP5XQmm3aQjtZ8vTXaYS3fTjP937ph"
EMAIL_HOST = "smtp.postmarkapp.com"
EMAIL_HOST_USER = "946b5cca-67cb-452c-84bb-fc9c27ceec0e"
EMAIL_HOST_PASSWORD = "946b5cca-67cb-452c-84bb-fc9c27ceec0e"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
SENDER_EMAIL = "Jason.mckittrick@fistream.com"
# Set up CORS
origins = [
    "*",
    # Add other origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust the allowed origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)


def get_db_connection():
    server = "dhpdevazsql01.database.windows.net"
    database = "dhpdevdb01"
    username = "dhpdevwebappdb01"
    password = "Z.M!EpvtWa!i233zq!pzyNP4Hkn4*CEKeeCwkcv4C"
    driver = "{ODBC Driver 17 for SQL Server}"

    connection_string = f"DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(connection_string)


def send_email(
    email_from: str, subject: str, body: str, cc: Optional[List[str]] = None
):
    try:
        # Set up the server
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls() if EMAIL_USE_TLS else None
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        # Create the email
        msg = MIMEMultipart()
        msg["From"] = email_from
        msg["To"] = SENDER_EMAIL
        msg["Subject"] = subject
        # Add CC addresses if provided
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg.attach(MIMEText(body, "plain"))
        recipients = cc if cc else []
        # Send the email
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@app.post("/step1", response_model=Step1Response)
async def step1(request: Step1Request):
    logging.info(
        f"Received Step 1 Request: {request.json()}"
    )  # Log incoming request data
    conn = get_db_connection()
    cursor = conn.cursor()

    params = (
        request.FirstName,
        request.LastName,
        request.ZipCode,
        request.Email,
        request.Phone,
        request.SellerID,
    )

    sql = """ 
    SET NOCOUNT ON;
    Declare @FirstName varchar(50),
            @LastName varchar(50),
            @ZipCode char(5),
            @Email varchar(100),
            @Phone varchar(20),
            @SellerId int
            
    Set		@FirstName = ?
    Set		@LastName = ?
    Set		@ZipCode = ?
    Set		@Email = ?
    Set		@Phone = ?
    Set  @SellerId = ?
    EXEC [Lead].Insert_EnrollmentLead @FirstName,@LastName,@ZipCode,@Email,@Phone,@SellerId;
    """

    try:
        cursor.execute(sql, *params)
        result = cursor.fetchone()
        logging.info(f"Raw result set: {result}")

        if result and len(result) == 1:
            data = json.loads(result[0])
            print(data)
            transaction_lead_uids = data["TransactionLeadUIDs"]
            zip_code_info = data["ZipCode"]
            # zip_code_info = json.loads(result[1]) if result[1] else None

            if zip_code_info is None:
                logging.warning("ZipCode query returned no results.")

            response = Step1Response(
                LeadID=transaction_lead_uids[0]["LeadID"],
                LeadUID=transaction_lead_uids[0]["LeadUID"],
                CityName=(
                    "" if zip_code_info[0] is None else zip_code_info[0]["CityName"]
                ),
                StateAbbreviation=(
                    ""
                    if zip_code_info[0] is None
                    else zip_code_info[0]["StateAbbreviation"]
                ),
            )

            logging.info(f"Step 1 Response: {response}")
            conn.commit()
            cursor.close()
            conn.close()
            logging.info(f"Step 1 Response sent successfully.")
            return response
        else:
            logging.info("Stored procedure did not return any results.")
            raise HTTPException(
                status_code=500, detail="Stored procedure did not return any results."
            )
    except pyodbc.Error as e:
        logging.error(f"Error executing Step 1 stored procedure: {e}")
        if cursor.messages:
            for message in cursor.messages:
                logging.error(message[1])
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step2", response_model=Step2Response)
async def step2(request: Step2Request):
    logging.info(
        f"Received Step 2 Request: {request.json()}"
    )  # Log incoming request data
    conn = get_db_connection()
    cursor = conn.cursor()

    def ensure_tinyint(value):
        return max(0, min(255, value))

    tinyint_params = {
        "PropertySQFT": ensure_tinyint(request.SqFt),
        "PropertyTypeID": ensure_tinyint(request.PropertyType),
        "PropertyStateID": ensure_tinyint(request.StateID),
        "ProductID": ensure_tinyint(request.PropertyType),
        "SellerID": ensure_tinyint(request.SellerID),
    }

    params_list = [
        request.FirstName,
        request.LastName,
        tinyint_params["PropertyTypeID"],
        tinyint_params["PropertySQFT"],
        request.PropertyAddress1,
        request.PropertyAddress2,
        request.City,
        tinyint_params["PropertyStateID"],
        request.ZipCode,
        request.Email,
        request.Phone,
        request.LeadUID,
        request.LeadID,
        tinyint_params["ProductID"],
        tinyint_params["SellerID"],
    ]

    sql = """
    SET NOCOUNT ON;
    DECLARE @FirstName VARCHAR(50), @LastName VARCHAR(50), @PropertyTypeID TINYINT, 
            @PropertySQFT INT, @PropertyStreetAddress1 VARCHAR(75), @PropertyStreetAddress2 VARCHAR(75), 
            @PropertyCity VARCHAR(50), @PropertyStateID TINYINT, @PropertyZipCode CHAR(5), 
            @Email VARCHAR(100), @Phone VARCHAR(20), @LeadUID UNIQUEIDENTIFIER, @LeadID INT, @ProductID TINYINT, @SellerID TINYINT;

    SET @FirstName = ?;
    SET @LastName = ?;
    SET @PropertyTypeID = ?;
    SET @PropertySQFT = ?;
    SET @PropertyStreetAddress1 = ?;
    SET @PropertyStreetAddress2 = ?;
    SET @PropertyCity = ?;
    SET @PropertyStateID = ?;
    SET @PropertyZipCode = ?;
    SET @Email = ?;
    SET @Phone = ?;
    SET @LeadUID = ?;
    SET @LeadID = ?;
    SET @ProductID = ?;
    SET @SellerID = ?;

    EXEC [Rates].get_QualifiedEnrollmentRate 
        @FirstName=@FirstName, @LastName=@LastName, @PropertyTypeID=@PropertyTypeID, 
        @PropertySQFT=@PropertySQFT, @PropertyStreetAddress1=@PropertyStreetAddress1, 
        @PropertyStreetAddress2=@PropertyStreetAddress2, @PropertyCity=@PropertyCity, 
        @PropertyStateID=@PropertyStateID, @PropertyZipCode=@PropertyZipCode, @Email=@Email, 
        @Phone=@Phone, @LeadUID=@LeadUID, @LeadID=@LeadID, @ProductID=@ProductID, @SellerID=@SellerID;
    SET NOCOUNT OFF;
    """
    try:
        cursor.execute(sql, params_list)

        # Fetch and process results
        result = cursor.fetchone()
        logging.info(f"Raw result set: {result}")

        if result:
            # Dynamically access the JSON key
            json_data = result[0]
            json_result = json.loads(json_data)

            rate_quote = json_result.get("RateQuote", [])
            options = json_result.get("Options", [])

            logging.info(f"Rate Quote: {rate_quote}")
            logging.info(f"Options: {options}")

            response = Step2Response(RateQuoted=rate_quote, Options=options)

            logging.info(f"Step 2 Response: {response}")

            # Commit the transaction
            conn.commit()

            # Close the connection
            cursor.close()
            conn.close()

            return response
        else:
            logging.info("Stored procedure did not return any results.")
            raise HTTPException(
                status_code=500, detail="Stored procedure did not return any results."
            )
    except pyodbc.Error as e:
        logging.error(f"Error executing Step 2 stored procedure: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step3")
async def step3(request: Step3Request):
    logging.info(
        f"Received Step 3 Request: {request.json()}"
    )  # Log incoming request data
    conn = get_db_connection()
    cursor = conn.cursor()

    # Convert RateQuoted items to JSON string
    quoted_details = json.dumps(request.RateQuoted)

    logging.info(f"Step 3 JSON to be sent to stored procedure: {quoted_details}")

    sql = "EXEC Rates.Insert_FullRateQuoted @QuotedDetails = ?"

    try:
        cursor.execute(sql, quoted_details)
        conn.commit()
        cursor.close()
        conn.close()
        response = {"message": "Stored procedure executed successfully."}
        logging.info(f"Step 3 Response: {response}")
        return response
    except pyodbc.Error as ex:
        logging.error(f"Error executing Step 3 stored procedure: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@app.post("/step4", response_model=Step4Response)
async def step4(request: Step4Request):
    print(request)
    logging.info(
        f"Received Step 4 Request: {request.json()}"
    )  # Log incoming request data
    conn = get_db_connection()
    cursor = conn.cursor()

    # Extracting and converting data from Step4Request
    billing_first_name = str(request.BillingFirstName)[:50]  # Limit to 50 characters
    billing_last_name = str(request.BillingLastName)[:50]  # Limit to 50 characters
    billing_address1 = str(request.BillingAddress1)[:75]  # Limit to 75 characters
    billing_address2 = str(request.BillingAddress2)[:75]  # Limit to 75 characters
    billing_city = str(request.BillingCity)[:50]  # Limit to 50 characters
    billing_state_id = int(request.BillingStateID)  # Convert to integer
    billing_zip_code = str(request.BillingZip)[:5]  # Limit to 5 characters
    billing_email = str(request.BillingEmail)[:100]  # Limit to 100 characters
    billing_phone = str(request.BillingPhone)[:20]  # Limit to 20 characters
    lead_id = int(request.LeadID)  # Convert to integer
    logging.error(f"Received Step 4 Request: {lead_id}")
    sql_insert = """
    EXEC [Rates].[Insert_EnrollmentBillingInfo]
        @BillingFirstName = ?,
        @BillingLastName = ?,
        @BillingStreetAddress1 = ?,
        @BillingStreetAddress2 = ?,
        @BillingCity = ?,
        @BillingStateID = ?,
        @BillingZipCode = ?,
        @BillingEmail = ?, 
        @BillingPhone = ?,
        @LeadID = ?
    """

    try:
        # Execute the stored procedure to insert billing info
        cursor.execute(
            sql_insert,
            (
                billing_first_name,
                billing_last_name,
                billing_address1,
                billing_address2,
                billing_city,
                billing_state_id,
                billing_zip_code,
                billing_email,
                billing_phone,
                lead_id,
            ),
        )
        conn.commit()
        logging.info("Billing information inserted successfully.")

        # Prepare data for payment
        customer_data = {
            "first_name": str(billing_first_name),
            "last_name": str(billing_last_name),
            "address1": str(billing_address1),
            "address2": str(billing_address2),
            "city": str(billing_city),
            "state": str(request.BillingStateAbbreviation),  # Use state abbreviation
            "zip": str(billing_zip_code),
            "ccnumber": str(request.ccnumber),  # Use lowercase attribute names
            "ccexp": str(request.ccexp),  # Use lowercase attribute names
            "cvv": str(request.cvv),  # Use lowercase attribute names
            "amount": str(request.totalAmount),
            "lead_id": str(lead_id),
            "lead_uid": str(request.LeadUID),
        }

        # Perform sale transaction
        response_code, response_data = perform_sale(API_KEY, customer_data)

        # Output response code and data
        logging.info("Response Code: %s", response_code)
        logging.info("Response Data: %s", response_data)

        # Check response code and handle accordingly
        if response_code == "1" or response_code == "100":
            # Execute the stored procedure to update sale information
            lead_uid = request.LeadUID
            response = response_data.get("response", "")
            response_text = response_data.get("responsetext", "")
            authorization_code = response_data.get("authcode", "")
            transaction_id = response_data.get("transactionid", "")
            avs_response = response_data.get("avsresponse", "")
            cvv_response = response_data.get("cvvresponse", "")
            order_id = response_data.get("orderid", "")
            transaction_type = response_data.get("type", "")
            response_code = response_data.get("response_code", "")
            amount_authorized = response_data.get("amount_authorized", "")
            customer_vault_id = (
                None  # You may need to extract this from the response if available
            )

            sql_update = """
            DECLARE @LeadID int,
                    @LeadUID uniqueidentifier,
                    @Response varchar(255),
                    @ResponseText varchar(255),
                    @AuthorizationCode varchar(255),
                    @TransactionID varchar(255),
                    @AVSResponse varchar(255),
                    @CVVResponse varchar(255),
                    @OrderID varchar(255),
                    @TransactionType varchar(255),
                    @ResponseCode varchar(255),
                    @AmountAuthorized varchar(255),
                    @CustomerVaultID varchar(255)

            SET @LeadID = ?
            SET @LeadUID = ?
            SET @Response = ?
            SET @ResponseText = ?
            SET @AuthorizationCode = ?
            SET @TransactionID = ?
            SET @AVSResponse = ?
            SET @CVVResponse = ?
            SET @OrderID = ?
            SET @TransactionType = ?
            SET @ResponseCode = ?
            SET @AmountAuthorized = ?
            SET @CustomerVaultID = ?

            EXEC Rates.Insert_CCNMIGatewayResponse @LeadID,
                                                   @LeadUID,
                                                   @Response,
                                                   @ResponseText,
                                                   @AuthorizationCode,
                                                   @TransactionID,
                                                   @AVSResponse,
                                                   @CVVResponse,
                                                   @OrderID,
                                                   @TransactionType,
                                                   @ResponseCode,
                                                   @AmountAuthorized,
                                                   @CustomerVaultID
            """

            cursor.execute(
                sql_update,
                (
                    lead_id,
                    lead_uid,
                    response,
                    response_text,
                    authorization_code,
                    transaction_id,
                    avs_response,
                    cvv_response,
                    order_id,
                    transaction_type,
                    response_code,
                    amount_authorized,
                    customer_vault_id,
                ),
            )
            conn.commit()
            logging.info("Payment information updated successfully.")

            # Include a message in the response
            response_data["message"] = "Payment successful."
            return response_data  # Return the payment gateway response
        else:
            logging.error("Payment failed with response code: %s", response_code)
            # Payment failed, raise HTTPException with appropriate status code and detail
            raise HTTPException(
                status_code=422, detail="Payment failed. Please try again later."
            )

    except pyodbc.Error as ex:
        # Log and raise an HTTPException in case of database error
        logging.error(f"Error executing Step 4 stored procedure: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        cursor.close()
        conn.close()


@app.post("/contact")
async def send_email_endpoint(email: EmailSchema):
    send_email(
        email.email_from,
        email.subject,
        email.body,
        ["jschmuck@diamondhomeprotection.com", "tkasick@diamondhomeprlotection.com"],
    )
    return {"message": "Email sent successfully"}


@app.post("/removedata")
async def remove_data(request: RemoveDataRequest):
    logging.info(
        f"Received Step 1 Request: {request.json()}"
    )  # Log incoming request data
    conn = get_db_connection()
    cursor = conn.cursor()

    params = (
        request.first_name,
        request.last_name,
        request.zipcode,
        request.email,
        request.phone,
        request.homeaddress,
        request.homecity,
        request.homestate,
        request.homezipcode,
    )
    sql = """ 
    SET NOCOUNT ON;
    EXEC Compliance.Insert_PersonalInformationRequest @FirstName=? @LastName=? @ZipCode=? @Email=? @Phone=? @HomeAddress=? @HomeCity=? @HomeState=? @HomeZipCode=?
    """

    try:
        cursor.execute(sql, *params)
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Stored procedure executed successfully."}
    except pyodbc.Error as e:
        logging.error(f"Error executing Step 1 stored procedure: {e}")
        if cursor.messages:
            for message in cursor.messages:
                logging.error(message[1])
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/getProperty")
async def getProperty():
    logging.info(f"Received Step 2 Request")  # Log incoming request data
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """ 
    SET NOCOUNT ON;
    EXEC [Ref].[Get_PropertyType]
    """
    try:
        cursor.execute(sql)
        result = cursor.fetchone()
        json_data = result[0]
        json_result = json.loads(json_data)
        logging.info(f"Raw result set: {result}")
        conn.commit()
        cursor.close()
        conn.close()
        return json_result
    except pyodbc.Error as e:
        logging.error(f"Error executing Step 1 stored procedure: {e}")
        if cursor.messages:
            for message in cursor.messages:
                logging.error(message[1])
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
