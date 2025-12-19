"""
Market-Rover 2.0 - Main Application Entry Point

A multi-agent stock intelligence system that monitors your portfolio,
scrapes news, analyzes sentiment, and generates weekly intelligence reports.

Now with parallel execution and HTML reports!
"""
import os
import argparse
from datetime import datetime
from pathlib import Path
from crew import create_crew
from config import GOOGLE_API_KEY, REPORT_DIR
import sys


def check_environment():
    """Check if environment is properly configured."""
    if not GOOGLE_API_KEY:
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment variables!")
        print("Please create a .env file with your Google API key.")
        print("Get a free key from: https://makersuite.google.com/app/apikey")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)


def save_report(report_content: str, export_format: str = 'html') -> Path:
    """
    Save the report in specified format (HTML by default).
    
    Args:
        report_content: The report text
        export_format: Format to save ('html', 'txt', 'csv')
        
    Returns:
        Path to saved report
    """
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if export_format == 'html':
        filename = f"market_rover_report_{timestamp}.html"
        filepath = REPORT_DIR / filename
        
        # Generate HTML report
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market-Rover 2.0 Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #1f2937;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 15px;
            text-align: center;
        }}
        .report-content {{
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            line-height: 1.8;
            color: #374151;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .timestamp {{
            color: #6b7280;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Market-Rover 2.0 Intelligence Report</h1>
            <p class="timestamp">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        <div class="report-content">{str(report_content)}</div>
    </div>
</body>
</html>
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    else:  # txt format
        filename = f"market_rover_report_{timestamp}.txt"
        filepath = REPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(" " * 25 + "MARKET-ROVER 2.0 INTELLIGENCE REPORT\n")
            f.write(" " * 30 + f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(str(report_content))
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("End of Report\n")
            f.write("=" * 80 + "\n")
    
    return filepath


def print_header():
    """Print application header."""
    print("=" * 80)
    print(" " * 25 + "🔍 MARKET-ROVER 2.0 🔍")
    print(" " * 18 + "AI-Powered Stock Intelligence System")
    print(" " * 25 + "⚡ Parallel Mode Enabled")
    print("=" * 80)
    print()


def main():
    """Main application entry point with CLI argument parsing."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Market-Rover 2.0 - Stock Intelligence System')
    parser.add_argument('--pdf', action='store_true', help='Generate PDF report (requires additional setup)')
    parser.add_argument('--csv-only', action='store_true', help='Export data as CSV only')
    parser.add_argument('--txt', action='store_true', help='Generate TXT report (legacy format)')
    args = parser.parse_args()
    
    # Determine export format
    if args.csv_only:
        export_format = 'csv'
    elif args.txt:
        export_format = 'txt'
    elif args.pdf:
        export_format = 'pdf'
    else:
        export_format = 'html'  # Default

def main_impl(export_format='html'):
    """Main application entry point."""
    try:
        # Print header
        print_header()
        
        # Check environment
        check_environment()
        
        print("📊 Initializing Market Rover Crew...")
        print()
        
        # Create and configure crew
        crew = create_crew()
        
        # Display crew information
        crew_info = crew.get_crew_info()
        print(f"Agents: {crew_info['num_agents']}")
        print(f"Tasks: {crew_info['num_tasks']}")
        print(f"Process: {crew_info['process']}")
        print(f"Max Iterations: {crew_info['max_iterations']}")
        print()
        print("Agent Roles:")
        for i, agent_type in enumerate(crew_info['agents'], 1):
            print(f"  {i}. {agent_type.replace('_', ' ').title()}")
        print()
        
        # Run the analysis
        print("🚀 Starting weekly portfolio analysis...")
        print("This may take a few minutes depending on portfolio size.")
        print()
        
        result = crew.run()
        
        # Save report
        print(f"\n📝 Saving report ({export_format.upper()} format)...")
        report_path = save_report(result, export_format)
        
        print(f"\n✅ Report saved to: {report_path}")
        print()
        
        # Print summary
        print("=" * 80)
        print("REPORT PREVIEW")
        print("=" * 80)
        print(str(result)[:500] + "..." if len(str(result)) > 500 else str(result))
        print("=" * 80)
        print()
        print(f"📄 Full report available at: {report_path}")
        print()
        print("Thank you for using Market Rover! 🚀")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='Market-Rover 2.0 - Stock Intelligence System')
    parser.add_argument('--pdf', action='store_true', help='Generate PDF report (requires additional setup)')
    parser.add_argument('--csv-only', action='store_true', help='Export data as CSV only')
    parser.add_argument('--txt', action='store_true', help='Generate TXT report (legacy format)')
    args = parser.parse_args()
    
    # Determine export format
    if args.csv_only:
        export_format = 'csv'
    elif args.txt:
        export_format = 'txt'
    elif args.pdf:
        print("⚠️  PDF export not yet implemented. Generating HTML instead.")
        export_format = 'html'
    else:
        export_format = 'html'  # Default
    
    main_impl(export_format)
