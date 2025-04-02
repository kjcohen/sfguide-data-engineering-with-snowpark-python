import sys
import os
import yaml
from collections import defaultdict

if len(sys.argv) < 3:
    print("Usage: python deploy_snowpark_apps.py <root_directory> <changed_files>")
    exit(1)

root_directory = sys.argv[1]
changed_files_path = sys.argv[2]

print(f"📦 Deploying updated Snowpark apps in: {root_directory}\n")

# Read changed files from GitHub Actions
with open(changed_files_path, 'r') as f:
    changed_files = [line.strip() for line in f.readlines() if line.strip()]

# Map project folders to the list of changed files within them
project_changes = defaultdict(list)

for file in changed_files:
    normalized_path = os.path.normpath(file)
    parts = normalized_path.split(os.sep)

    # Only track files under steps/{project}/...
    if len(parts) >= 3 and parts[0] == 'steps':
        project_name = parts[1]
        project_dir = os.path.join(root_directory, 'steps', project_name)
        full_file_path = os.path.join('steps', project_name, *parts[2:])
        project_changes[project_dir].append(full_file_path)

if not project_changes:
    print("✅ No updated Snowpark projects found. Skipping deployment.")
    exit(0)

# Deploy each updated project
for project_path in sorted(project_changes.keys()):
    project_name = os.path.basename(project_path)
    changed = project_changes[project_path]

    print(f"🚀 Deploying project: {project_name}")
    print(f"📁 Path: {project_path}")
    print("📝 Changed files:")
    for file in changed:
        print(f"   - {file}")

    # Change to project directory and deploys
    os.chdir(project_path)
    print("🔧 Building project...")
    os.system(f"snow snowpark build --temporary-connection --account $SNOWFLAKE_ACCOUNT --user $SNOWFLAKE_USER --role $SNOWFLAKE_ROLE --warehouse $SNOWFLAKE_WAREHOUSE --database $SNOWFLAKE_DATABASE")

    print("🚢 Deploying project...")
    os.system(f"snow snowpark deploy --replace --temporary-connection --account $SNOWFLAKE_ACCOUNT --user $SNOWFLAKE_USER --role $SNOWFLAKE_ROLE --warehouse $SNOWFLAKE_WAREHOUSE --database $SNOWFLAKE_DATABASE")
    print("✅ Deployment complete.\n")

print("🎉 All updated Snowpark projects have been deployed.")
