from pydantic import BaseModel,ConfigDict
class OfferCreate(BaseModel):
    company_name:str
    company_address:str
    company_email:str
    company_phone:str
    candidate_name:str
    candidate_address:str
    email:str
    phone:str
    designation:str
    department:str
    joining_date:str
    work_location:str
    employment_type:str
    ctc:float
    probation_period:str
    notice_period:str
    reporting_to:str
    hr_name:str
class OfferResponse(OfferCreate):
    id:int; offer_number:str; status:str; pdf_path:str|None=None
    model_config=ConfigDict(from_attributes=True)
