import sys
import os
import yaml

ignore_folders = {'.git', '__pycache__', '.ipynb_checkpoints'}
snowflake_project_config_filename = 'snowflake.yml'

if len(sys.argv) < 3:
    print("Usage: python deploy_snowpark_apps.py <root_directory> <changed_files>")
    exit(1)

root_directory = sys.argv[1]
changed_files_path = sys.argv[2]

print(f"Deploying only updated Snowpark apps in {root_directory}")

# Read changed files from the GitHub Actions step
with open(changed_files_path, 'r') as f:
    changed_files = {line.strip() for line in f.readlines() if line.strip()}

def find_project_root(file_path):
    """Finds the nearest directory containing snowflake.yml from a given file path."""
    project_dir = os.path.dirname(file_path)
    while project_dir and project_dir != root_directory:
        config_path = os.path.join(project_dir, snowflake_project_config_filename)
        if os.path.exists(config_path):
            return project_dir  # Return the first directory where snowflake.yml is found
        project_dir = os.path.dirname(project_dir)  # Move up a level
    return None  # No valid project found

# Extract unique project directories containing changed files
updated_projects = set()
for file in changed_files:
    project_root = find_project_root(file)
    if project_root:
        updated_projects.add(project_root)

if not updated_projects:
    print("No updated Snowpark projects found. Skipping deployment.")
    exit(0)

for project_path in sorted(updated_projects):
    print(f"Processing Snowflake project in {project_path}")

    config_path = os.path.join(project_path, snowflake_project_config_filename)
    if not os.path.exists(config_path):
        print(f"Skipping {project_path}, no {snowflake_project_config_filename} found.")
        continue  # Prevents errors if a subfolder is detected incorrectly

    # Read project configuration
    with open(config_path, "r") as yamlfile:
        project_settings = yaml.load(yamlfile, Loader=yaml.FullLoader)

    # Ensure it's a Snowpark project
    if 'snowpark' not in project_settings:
        print(f"Skipping non-Snowpark project: {project_path}")
        continue

    project_name = project_settings['snowpark'].get('project_name', 'Unnamed')
    print(f"Deploying Snowpark project: {project_name}")

    os.chdir(project_path)
    os.system(f"snow snowpark build --temporary-connection --account $SNOWFLAKE_ACCOUNT --user $SNOWFLAKE_USER --role $SNOWFLAKE_ROLE --warehouse $SNOWFLAKE_WAREHOUSE --database $SNOWFLAKE_DATABASE")
    os.system(f"snow snowpark deploy --replace --temporary-connection --account $SNOWFLAKE_ACCOUNT --user $SNOWFLAKE_USER --role $SNOWFLAKE_ROLE --warehouse $SNOWFLAKE_WAREHOUSE --database $SNOWFLAKE_DATABASE")

print("Deployment complete.")
