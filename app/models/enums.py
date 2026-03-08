"""
Enums for the application.
"""

from enum import Enum


class JobStatus(str, Enum):
    """
    Job status enum.
    """

    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWED = "interviewed"
    REJECTED = "rejected"
    IRRELEVANT = "irrelevant"
