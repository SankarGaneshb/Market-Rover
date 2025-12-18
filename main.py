"""
Market Rover - Main Application Entry Point

A multi-agent stock intelligence system that monitors your portfolio,
scrapes news, analyzes sentiment, and generates weekly intelligence reports.
"""
import os
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


def save_report(report_content: str) -> Path:
    """
    Save the report to a file.
    
    Args:
        report_content: The report text
        
    Returns:
        Path to saved report
    """
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_rover_report_{timestamp}.txt"
    filepath = REPORT_DIR / filename
    
    # Save report
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(" " * 25 + "MARKET ROVER INTELLIGENCE REPORT\n")
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
    print(" " * 25 + "🔍 MARKET ROVER 🔍")
    print(" " * 20 + "Crew Intelligence Agent System")
    print("=" * 80)
    print()


def main():
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
        print("\n📝 Saving report...")
        report_path = save_report(result)
        
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
    main()
