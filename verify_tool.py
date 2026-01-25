import sys
import os

sys.path.append(os.getcwd())

try:
    from rover_tools.forensic_tool import check_accounting_fraud
    # CrewAI tools usually inherit from langchain_core.tools.BaseTool but checked via Pydantic
    print(f"Tool imported successfully: {check_accounting_fraud}")
    print(f"Tool type: {type(check_accounting_fraud)}")
    
    # Check if it has 'name' and 'description' which are required
    print(f"Name: {check_accounting_fraud.name}")
    print(f"Description: {check_accounting_fraud.description}")
    
    # Try to validate it against CrewAI's expected type if possible, 
    # but successful import and property access is a good sign
    print("VERIFICATION SUCCESSFUL")

except Exception as e:
    print(f"VERIFICATION FAILED: {e}")
