
import os
import sys

TARGET_FILE = "tools/derivative_analysis.py"

OLD_BLOCK = """            # Logic: Strategy predicts an Annualized Growth Rate
            # We compare this with the Actual Annual Return of test_year
            
            start_price = test_df.iloc[0]['Open']
            end_price = test_df.iloc[-1]['Close']
            
            if start_price == 0: continue
            
            # Actual ROI for the specific period captured in test_df
            actual_return = ((end_price / start_price) - 1) * 100
            
            # Error = |Actual - Predicted|
            err_med = abs(actual_return - res_med['annualized_growth'])
            err_sd = abs(actual_return - res_sd['annualized_growth'])
            
            errors['median'].append(err_med)
            errors['sd'].append(err_sd)
            tested_years.append(test_year)"""

NEW_BLOCK = """            # Compare Returns via Price Difference
            end_price = test_df.iloc[-1]['Close']
            
            def get_price_at_date(path, target_dt):
                if not path: return None
                closest = min(path, key=lambda x: abs((x['date'] - target_dt).days))
                return closest['price']

            # Use projection path if available
            target_dt = test_df.index[-1]
            path_med = res_med.get('projection_path')
            path_sd = res_sd.get('projection_path')
            
            pred_med = get_price_at_date(path_med, target_dt) if path_med else res_med['forecast_price']
            pred_sd = get_price_at_date(path_sd, target_dt) if path_sd else res_sd['forecast_price']
                
            # Error %
            err_med = abs((pred_med - end_price) / end_price) * 100
            err_sd = abs((pred_sd - end_price) / end_price) * 100
            
            errors['median'].append(err_med)
            errors['sd'].append(err_sd)
            tested_years.append(test_year)"""

def patch_file():
    if not os.path.exists(TARGET_FILE):
        print(f"Error: {TARGET_FILE} not found")
        sys.exit(1)

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Normalize line endings for search
    # We'll just strip valid whitespace from the block ends
    
    if OLD_BLOCK not in content:
        print("Error: Block not found in file. Content might have drifted.")
        # Debug: Print a snippet where it should be
        idx = content.find("Logic: Strategy predicts")
        if idx != -1:
            print(f"Found something similar at index {idx}:")
            print(content[idx:idx+200])
        else:
            print("Could not find 'Logic: Strategy predicts' at all.")
        sys.exit(1)

    new_content = content.replace(OLD_BLOCK, NEW_BLOCK)

    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Success: Patch applied.")

if __name__ == "__main__":
    patch_file()
