"""
here we define the declarative base instance
from which all orm models will inherit
"""

from sqlalchemy.ext import declarative

Base = declarative.declarative_base()
