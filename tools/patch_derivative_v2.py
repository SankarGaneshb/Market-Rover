
import os
import sys
import re

TARGET_FILE = "tools/derivative_analysis.py"

def patch_file():
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1

    for i, line in enumerate(lines):
        if "start_price = test_df.iloc[0]['Open']" in line:
            start_idx = i
        if "tested_years.append(test_year)" in line and start_idx != -1:
            end_idx = i
            break
    
    if start_idx == -1 or end_idx == -1:
        print("Error: Could not find strict start/end markers.")
        sys.exit(1)

    print(f"Replacing lines {start_idx} to {end_idx}")

    # Construct revised block
    # We need to maintain indentation of the start line
    indent = lines[start_idx][:lines[start_idx].find("start_price")]
    
    new_block_lines = [
        f"{indent}# Compare Returns via Price Difference\n",
        f"{indent}end_price = test_df.iloc[-1]['Close']\n",
        f"{indent}\n",
        f"{indent}def get_price_at_date(path, target_dt):\n",
        f"{indent}    if not path: return None\n",
        f"{indent}    closest = min(path, key=lambda x: abs((x['date'] - target_dt).days))\n",
        f"{indent}    return closest['price']\n",
        f"{indent}\n",
        f"{indent}# Use projection path if available\n",
        f"{indent}target_dt = test_df.index[-1]\n",
        f"{indent}path_med = res_med.get('projection_path')\n",
        f"{indent}path_sd = res_sd.get('projection_path')\n",
        f"{indent}\n",
        f"{indent}pred_med = get_price_at_date(path_med, target_dt) if path_med else res_med['forecast_price']\n",
        f"{indent}pred_sd = get_price_at_date(path_sd, target_dt) if path_sd else res_sd['forecast_price']\n",
        f"{indent}    \n",
        f"{indent}# Error %\n",
        f"{indent}err_med = abs((pred_med - end_price) / end_price) * 100\n",
        f"{indent}err_sd = abs((pred_sd - end_price) / end_price) * 100\n",
        f"{indent}\n",
        f"{indent}errors['median'].append(err_med)\n",
        f"{indent}errors['sd'].append(err_sd)\n"
    ]

    # Replace in list
    # remove old lines from start_idx to end_idx-1 (keep the append line at end_idx? No, my new block ends right before it)
    # The original block ended with `tested_years.append`. I should check if I included it in new block.
    # My NEW_BLOCK above ends with `errors['sd']...`. It does NOT include `tested_years.append`.
    # So I should replace up to `end_idx` (exclusive).
    
    final_lines = lines[:start_idx] + new_block_lines + lines[end_idx:]
    
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

    print("Success: Patched via line replacement.")

if __name__ == "__main__":
    patch_file()
