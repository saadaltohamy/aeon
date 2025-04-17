#!/usr/bin/env python3
"""Allow contributors to add/remove labels via comment commands on PRs."""
# test branch 2
import json
import os
import re
import sys

from github import Github

# Load GitHub context
context = json.loads(os.getenv("CONTEXT_GITHUB", "{}"))
repo_name = context["repository"]
event = context["event"]

# Authenticate
g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo(repo_name)

# Only run on PR comments
issue_payload = event.get("issue", {})
if "pull_request" not in issue_payload:
    sys.exit(0)

# Extract PR number and comment
pr_number = issue_payload["number"]
comment_body = event["comment"]["body"]
comment_user = event["comment"]["user"]["login"]

# Get the PR object
pr = repo.get_pull(number=pr_number)

# Only respond when bot is mentioned
if "@aeon-actions-bot" not in comment_body.lower():
    sys.exit(0)

# Build a map of valid labels (lower → real case)
valid_labels = {lbl.name.lower(): lbl.name for lbl in repo.get_labels()}

# Parse add/remove commands
add_raw = re.findall(r'add label[s]?\s+"([^"]+)"', comment_body, flags=re.IGNORECASE)
remove_raw = re.findall(
    r'remove label[s]?\s+"([^"]+)"', comment_body, flags=re.IGNORECASE
)

# Match against actual labels
add_labels = [
    valid_labels[lbl.lower()] for lbl in add_raw if lbl.lower() in valid_labels
]
remove_labels = [
    valid_labels[lbl.lower()] for lbl in remove_raw if lbl.lower() in valid_labels
]

# Apply adds
for label in add_labels:
    pr.add_to_labels(label)

# Apply removals
for label in remove_labels:
    pr.remove_from_labels(label)

# If nothing matched, leave a hint
if not add_labels and not remove_labels:
    pr.create_issue_comment(
        "👋 I couldn't find any valid label commands in your comment.\n\n"
        "Usage:\n"
        '`@aeon-actions-bot add label "label-name"`\n'
        '`@aeon-actions-bot remove label "label-name"`\n\n'
        "Make sure the label exists in the repository and is spelled exactly."
    )
