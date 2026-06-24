import os

# app.py fails closed if SECRET_KEY is unset. Inject an ephemeral, random
# secret for the test process so imports succeed — never a real or fixed value.
os.environ.setdefault("SECRET_KEY", os.urandom(16).hex())
