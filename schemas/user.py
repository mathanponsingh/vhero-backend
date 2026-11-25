from pydantic import BaseModel

class Email_Schema(BaseModel):
    email : str

class Otp_Verify_Schema(BaseModel):
    email: str
    otp: int