
import streamlit_authenticator as stauth
import inspect

print("Version:", stauth.__version__)
print("\nLogin Signature:")
try:
    print(inspect.signature(stauth.Authenticate.login))
except:
    print("Could not get signature")

print("\nLogin Docstring:")
print(stauth.Authenticate.login.__doc__)
