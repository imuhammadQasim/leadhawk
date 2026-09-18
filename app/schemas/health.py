#Jab hum check karna chahte hain ke API/application properly chal rahi hai ya nahi, to HealthResponse batata hai ke response ka format kya hoga.

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app_name: str
    environment: str
