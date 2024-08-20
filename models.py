from pydantic import BaseModel
from typing import List, Dict, Union, Optional

class RateQuotedItem(BaseModel):
    LeadID: int
    ReserveID: int
    RateQuote: float

class OptionItem(BaseModel):
    ReserveId: int
    ReserveDescription: str
    ReserveAmount: float

class Step2Response(BaseModel):
    RateQuoted: List[RateQuotedItem]
    Options: List[OptionItem]

class Step1Request(BaseModel):
    FirstName: str
    LastName: str
    ZipCode: str
    Email: str
    Phone: str
    SellerID: int

class Step1Response(BaseModel):
    LeadID: int
    LeadUID: str
    CityName: str
    StateAbbreviation: str

class Step2Request(BaseModel):
    LeadID: int
    LeadUID: str
    PropertyType: int
    PropertyAddress1: str
    PropertyAddress2: str
    City: str
    StateID: int
    SqFt: int
    FirstName: str
    LastName: str
    ZipCode: str
    Email: str
    Phone: str
    SellerID: int

class Step3Request(BaseModel):
    RateQuoted: List[Dict[str, Union[int, float]]]

class Step4Request(BaseModel):
    LeadID: int
    LeadUID: str
    totalAmount: int
    BillingFirstName: str
    BillingLastName: str
    BillingAddress1: str
    BillingAddress2: str
    BillingCity: str
    BillingStateID: int 
    BillingZip: str
    BillingPhone: str
    BillingEmail: str
    ccnumber: str  # Updated key to match the data
    ccexp: str     # Updated key to match the data
    cvv: str       # Updated key to match the data
    BillingStateAbbreviation: str

class Step4Response(BaseModel):
    response: str
    responsetext: str
    authcode: str
    transactionid: str
    avsresponse: Optional[str]
    cvvresponse: Optional[str]
    orderid: str
    type: str
    response_code: str
    amount_authorized: str
    message: str