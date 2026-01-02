"""
CLI Wrapper for Market-Rover Workflow Tracking
Usage:
    python -m utils.tracking start <workflow_name>
    python -m utils.tracking stop <session_id> [success|failed]
    python -m utils.tracking event <event_type> <description>
"""
import sys
import argparse
from utils.metrics import track_workflow_start, track_workflow_end, track_workflow_event

def main():
    parser = argparse.ArgumentParser(description="Market-Rover Workflow Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Start Command
    start_parser = subparsers.add_parser("start", help="Start a workflow session")
    start_parser.add_argument("name", help="Name of the workflow (e.g. feature-dev)")

    # Stop Command
    stop_parser = subparsers.add_parser("stop", help="Stop a workflow session")
    stop_parser.add_argument("session_id", help="Session ID returned by start")
    stop_parser.add_argument("status", nargs="?", default="success", help="Status (success/failed)")

    # Event Command
    event_parser = subparsers.add_parser("event", help="Log a point-in-time event")
    event_parser.add_argument("type", help="Event type (e.g. flexibility_protocol)")
    event_parser.add_argument("description", help="Description or reason")

    args = parser.parse_args()

    if args.command == "start":
        session_id = track_workflow_start(args.name)
        print(f"Session Started: {session_id}")
        print(f"To stop: python -m utils.tracking stop {session_id} success")
    
    elif args.command == "stop":
        track_workflow_end(args.session_id, args.status)
        print(f"Session {args.session_id} ended with status: {args.status}")

    elif args.command == "event":
        track_workflow_event(args.type, args.description)
        print(f"Event logged: {args.type}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
