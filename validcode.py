#!/usr/bin/env python3
# to test function to check for valid subject code
import string
valid_chars='{}{}'.format(string.ascii_letters,string.digits)
testnm='00123'

def validcode(testnm):
    valid_chars='{}{}'.format(string.ascii_letters,string.digits)
    valid = True
    for c in testnm:
        if c not in valid_chars:
            valid = False
            break
    return valid

print(validcode(testnm))
