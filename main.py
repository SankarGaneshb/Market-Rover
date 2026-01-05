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
from crew_engine import create_crew
from config import GOOGLE_API_KEY, REPORT_DIR
from utils.logger import get_logger

logger = get_logger(__name__)
import sys
from agents import create_visualizer_agent
from tasks import create_market_snapshot_task
from crewai import Crew, Process


def check_environment():
    """Check if environment is properly configured."""
    if not GOOGLE_API_KEY:
        logger.warning("⚠️  WARNING: GOOGLE_API_KEY not found in environment variables!")
        logger.info("Please create a .env file with your Google API key.")
        logger.info("Get a free key from: https://makersuite.google.com/app/apikey")
        logger.info("")
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
    """Log application header."""
    logger.info("%s", "=" * 80)
    logger.info("%s", " " * 25 + "🔍 MARKET-ROVER 2.0 🔍")
    logger.info("%s", " " * 18 + "AI-Powered Stock Intelligence System")
    logger.info("%s", " " * 25 + "⚡ Parallel Mode Enabled")
    logger.info("%s", "=" * 80)
    logger.info("")


def main():
    """Main application entry point with CLI argument parsing."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Market-Rover - Stock Intelligence System')
    parser.add_argument('--pdf', action='store_true', help='Generate PDF report (requires additional setup)')
    parser.add_argument('--csv-only', action='store_true', help='Export data as CSV only')
    parser.add_argument('--txt', action='store_true', help='Generate TXT report (legacy format)')
    parser.add_argument('--visualize', type=str, help='Generate Market Snapshot for a specific ticker (e.g., SBIN)')
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

        export_format = 'html'  # Default
    
    # Handle Visualizer Mode
    if args.visualize:
        run_visualizer(args.visualize)
        return

def run_visualizer(ticker):
    """Runs the Visualizer Agent for a specific ticker."""
    from utils.visualizer_interface import generate_market_snapshot
    
    print_header()
    logger.info("🎨 Starting Market Rover Visualizer for %s...", ticker)

    result = generate_market_snapshot(ticker)

    logger.info("%s", "\n" + "=" * 60)
    if result['success']:
        logger.info("✅ Visualization Complete!")
        logger.info(result['message'])
        if result['image_path']:
            logger.info("\nDashboard saved to: %s", result['image_path'])
    else:
        logger.error("❌ Visualization Failed!")
        logger.error(result['message'])
    logger.info("%s", "=" * 60)

def main_impl(export_format='html'):
    """Main application entry point."""
    try:
        # Print header
        print_header()

        # Check environment
        check_environment()

        logger.info("📊 Initializing Market Rover Crew...")
        logger.info("")
        
        # Create and configure crew
        crew = create_crew()
        
        # Display crew information
        crew_info = crew.get_crew_info()
        logger.info("Agents: %s", crew_info['num_agents'])
        logger.info("Tasks: %s", crew_info['num_tasks'])
        logger.info("Process: %s", crew_info['process'])
        logger.info("Max Iterations: %s", crew_info['max_iterations'])
        logger.info("")
        logger.info("Agent Roles:")
        for i, agent_type in enumerate(crew_info['agents'], 1):
            logger.info("  %s. %s", i, agent_type.replace('_', ' ').title())
        logger.info("")

        # Run the analysis
        logger.info("🚀 Starting weekly portfolio analysis...")
        logger.info("This may take a few minutes depending on portfolio size.")
        logger.info("")
        
        result = crew.run()
        
        # Save report
        logger.info("\n📝 Saving report (%s format)...", export_format.upper())
        report_path = save_report(result, export_format)

        logger.info("\n✅ Report saved to: %s", report_path)
        logger.info("")
        
        # Print summary
        logger.info("%s", "=" * 80)
        logger.info("REPORT PREVIEW")
        logger.info("%s", "=" * 80)
        logger.info(str(result)[:500] + "..." if len(str(result)) > 500 else str(result))
        logger.info("%s", "=" * 80)
        logger.info("")
        logger.info("📄 Full report available at: %s", report_path)
        logger.info("")
        logger.info("Thank you for using Market Rover! 🚀")
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Analysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception("\n❌ Error: %s", str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='Market-Rover 2.0 - Stock Intelligence System')
    parser.add_argument('--pdf', action='store_true', help='Generate PDF report (requires additional setup)')
    parser.add_argument('--csv-only', action='store_true', help='Export data as CSV only')
    parser.add_argument('--txt', action='store_true', help='Generate TXT report (legacy format)')
    parser.add_argument('--visualize', type=str, help='Generate Market Snapshot for a specific ticker (e.g., SBIN)')
    args = parser.parse_args()
    
    # Determine export format
    if args.csv_only:
        export_format = 'csv'
    elif args.txt:
        export_format = 'txt'
    elif args.pdf:
        logger.warning("⚠️  PDF export not yet implemented. Generating HTML instead.")
        export_format = 'html'
    # Handle Visualizer Mode
    if args.visualize:
        run_visualizer(args.visualize)
    else:
        main_impl(export_format)
