import xml.etree.ElementTree as ET
import os

try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    
    files = []
    
    for package in root.findall('.//package'):
        for class_node in package.findall('.//class'):
            filename = class_node.get('filename')
            line_rate = float(class_node.get('line-rate'))
            
            # Count lines
            lines = class_node.findall('.//line')
            total_lines = len(lines)
            missed_lines = 0
            for line in lines:
                if int(line.get('hits')) == 0:
                    missed_lines += 1
            
            files.append({
                'filename': filename,
                'coverage': line_rate * 100,
                'total': total_lines,
                'missed': missed_lines
            })
            
    # Sort by missed lines (descending) - these hurt coverage the most
    files.sort(key=lambda x: x['missed'], reverse=True)
    
    with open('coverage_report.txt', 'w') as out:
        out.write(f"{'Filename':<50} | {'Cov%':<6} | {'Missed':<6} | {'Total':<6}\n")
        out.write("-" * 80 + "\n")
        
        count = 0
        for f in files:
            if count >= 30: break
            out.write(f"{f['filename']:<50} | {f['coverage']:5.1f}% | {f['missed']:<6} | {f['total']:<6}\n")
            count += 1
            
        out.write(f"\nTotal Files tracked: {len(files)}\n")
    print("Report saved to coverage_report.txt")

except Exception as e:
    print(f"Error parsing coverage.xml: {e}")
