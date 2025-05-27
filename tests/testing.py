import os

try :
    lm = os.environ['ACE']
except Exception as e:
    print("nothing found")