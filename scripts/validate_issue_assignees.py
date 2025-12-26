#!/usr/bin/env python3
"""Validate GITHUB_ISSUE_ASSIGNEES and GITHUB_ISSUE_LABELS formatting.

Exit codes:
  0 = OK
  2 = Invalid format
"""
import os
import re
import sys


def valid_github_username(u: str) -> bool:
    # GitHub usernames may only contain alphanumeric characters or hyphens,
    # cannot have multiple consecutive hyphens at ends, and <=39 chars.
    u = u.strip()
    if not u:
        return False
    if len(u) > 39:
        return False
    # Must not start or end with hyphen
    if u[0] == '-' or u[-1] == '-':
        return False
    if not re.match(r'^[A-Za-z0-9-]+$', u):
        return False
    return True


def valid_label(l: str) -> bool:
    # Allow letters, numbers, hyphen, underscore, slash and colon (common label formats)
    l = l.strip()
    if not l:
        return False
    return bool(re.match(r'^[A-Za-z0-9_\-/:]+$', l))


def main():
    assignees = os.getenv('GITHUB_ISSUE_ASSIGNEES', '')
    labels = os.getenv('GITHUB_ISSUE_LABELS', '')

    ok = True

    if assignees:
        items = [s.strip() for s in assignees.split(',') if s.strip()]
        invalid = [s for s in items if not valid_github_username(s)]
        if invalid:
            print('Invalid GitHub assignee(s) found:', invalid)
            ok = False
        else:
            print('Assignees look valid:', items)
    else:
        print('No GITHUB_ISSUE_ASSIGNEES set; skipping assignee validation (OK).')

    if labels:
        items = [s.strip() for s in labels.split(',') if s.strip()]
        invalid = [s for s in items if not valid_label(s)]
        if invalid:
            print('Invalid label(s) found:', invalid)
            ok = False
        else:
            print('Labels look valid:', items)
    else:
        print('No GITHUB_ISSUE_LABELS set; skipping label validation (OK).')

    if not ok:
        print('\nValidation failed: please correct the secret values. See README for expected formats.')
        sys.exit(2)

    print('\nValidation passed.')
    sys.exit(0)


if __name__ == '__main__':
    main()
