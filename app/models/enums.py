# app/models/enums.py
from enum import Enum

class JobStatus(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWED = "interviewed"
    REJECTED = "rejected"
    IRRELEVANT = "irrelevant"