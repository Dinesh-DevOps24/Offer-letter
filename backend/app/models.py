from sqlalchemy import Column,Integer,String,Float
from .database import Base
class Offer(Base):
    __tablename__="offers"
    id=Column(Integer,primary_key=True)
    offer_number=Column(String,unique=True,index=True)
    company_name=Column(String); company_address=Column(String); company_email=Column(String); company_phone=Column(String)
    candidate_name=Column(String); candidate_address=Column(String); email=Column(String); phone=Column(String)
    designation=Column(String); department=Column(String); joining_date=Column(String); work_location=Column(String)
    employment_type=Column(String); ctc=Column(Float); probation_period=Column(String); notice_period=Column(String)
    reporting_to=Column(String); hr_name=Column(String); status=Column(String,default="ACTIVE")
    pdf_path=Column(String); signature=Column(String)
