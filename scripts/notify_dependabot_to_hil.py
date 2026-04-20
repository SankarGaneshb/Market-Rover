import os
import sys
import argparse
from rover_tools.hil_client import notify_hil

def main():
    parser = argparse.ArgumentParser(description="Notify HIL Dashboard about Dependabot PRs")
    parser.add_argument("--pr-number", required=True, help="GitHub PR Number")
    parser.add_argument("--pr-title", required=True, help="GitHub PR Title")
    parser.add_argument("--pr-url", required=True, help="GitHub PR URL")
    parser.add_argument("--update-type", required=True, help="Dependabot update type (major/minor/patch)")
    parser.add_argument("--is-auto-merged", action="store_true", help="Whether the PR was auto-merged")

    args = parser.parse_args()

    agent_name = "SRE Support (Dependency Guard)"
    task_name = f"Dependabot PR #{args.pr_number}"

    status = "APPROVED" if args.is_auto_merged else "PENDING"

    instructions = (
        f"Dependabot has proposed an update: {args.pr_title}\n"
        f"Update Type: {args.update_type.upper()}\n"
        f"PR Link: {args.pr_url}\n"
    )

    if args.is_auto_merged:
        instructions += "\n[ACTION] This PR has been AUTO-APPROVED and MERGED as per policy (Minor/Patch)."
    else:
        instructions += "\n[ACTION] This is a MAJOR update. Manual review is REQUIRED in GitHub before merging."

    data = {
        "pr_number": args.pr_number,
        "pr_title": args.pr_title,
        "pr_url": args.pr_url,
        "update_type": args.update_type,
        "auto_merged": args.is_auto_merged,
        "policy": "Auto-merge Minor/Patch, Manual Major"
    }

    print(f"[HIL SYNC] Notifying Mission Control about PR #{args.pr_number}...")
    result = notify_hil(
        agent_name=agent_name,
        task_name=task_name,
        instructions=instructions,
        data=data,
        status=status
    )

    if result:
        print(f"[HIL SYNC] Successfully logged PR #{args.pr_number} in HIL Dashboard.")
    else:
        print(f"[HIL SYNC] Failed to notify HIL Dashboard.")

if __name__ == "__main__":
    main()
