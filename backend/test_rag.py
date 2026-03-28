import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.database import SessionLocal
from db.models import FAQItem
import re

def test_rag_logic():
    print("Testing RAG logic...")
    user_query = "Hi, can you tell me what tone rules we have?"
    words = [w for w in re.findall(r'\w+', user_query.lower()) if len(w) >= 3]
    if not words:
        words = [user_query.lower()]
    
    print(f"Query: {user_query}")
    print(f"Words extracted: {words}")
    
    if "rules" in words and "tone" in words:
        print("Success: Keywords correctly extracted for DB search")
    else:
        print("Error: Keywords not extracted correctly")

if __name__ == "__main__":
    test_rag_logic()
