
import streamlit_authenticator as stauth
import inspect

print("Attributes:", dir(stauth))

if hasattr(stauth, 'Authenticate'):
    print("\nAuthenticate methods:", dir(stauth.Authenticate))
    if hasattr(stauth.Authenticate, 'login'):
        print("\nLogin Signature:")
        try:
            print(inspect.signature(stauth.Authenticate.login))
        except:
            print("Could not get signature")
else:
    print("Authenticate class not found")
