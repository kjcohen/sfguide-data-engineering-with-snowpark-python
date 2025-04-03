import sys
import os
import yaml
import json
import boto3
import tempfile
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import logging
from botocore.exceptions import BotoCoreError, ClientError

# === CONFIG ===
SECRET_NAME = 'KeyPairs'
AWS_REGION = 'us-east-1'

SNOWFLAKE_USER = 'HRSFT_MIGRATION_USER'
SNOWFLAKE_WAREHOUSE = 'COMPUTE_WH'
ENV_TO_DB = {
    'dev': 'DEVELOPMENT',
    'qa': 'QA',
    'prod': 'PROD'
}

def write_private_key_to_pem_file(private_key_pem, passphrase):
    """
    Converts an encrypted PEM key to unencrypted PKCS#8 PEM format.
    Writes to a temp file and returns its path (Snow CLI-compatible on Windows).
    """
    try:
        private_key_pem = private_key_pem.strip().replace("\\n", "\n")
        private_key_obj = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=passphrase.encode() if passphrase else None,
            backend=default_backend()
        )

        pem_data = private_key_obj.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        temp_key_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w", encoding="utf-8")
        temp_key_file.write(pem_data.decode())
        temp_key_file.close()

        print(f"[DEBUG] Unencrypted PEM key written to: {temp_key_file.name}")
        return temp_key_file.name

    except Exception as e:
        logging.error(f"❌ Error preparing private key: {e}")
        raise

def load_secret():
    client = boto3.client('secretsmanager', region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=SECRET_NAME)
    return json.loads(response['SecretString'])

def configure_snowflake_env_vars(target_env):
    if "_" not in target_env:
        raise ValueError("Invalid environment format. Use <client>_<env> (e.g. wheels_dev)")

    client, env = target_env.split("_", 1)
    env = env.lower()

    if env not in ENV_TO_DB:
        raise ValueError(f"Invalid env '{env}'. Must be one of: {', '.join(ENV_TO_DB)}")

    secrets = load_secret()

    account = secrets[f"{client.upper()}_MIG_ACCOUNT"]
    role = secrets[f"{client.upper()}_MIG_ROLE"]
    private_key_pem = secrets[f"{client.upper()}_MIG_PRIVATE"]
    passphrase = secrets[f"{client.upper()}_MIG_PASSPHRASE"]
    database = ENV_TO_DB[env]

    # Prepare key file for Snow CLI
    key_path = write_private_key_to_pem_file(private_key_pem, passphrase)

    # Unset the raw key to avoid Snow CLI conflicts
    os.environ.pop("SNOWFLAKE_PRIVATE_KEY", None)

    # Set environment variables
    os.environ["SNOWFLAKE_USER"] = SNOWFLAKE_USER
    os.environ["SNOWFLAKE_AUTHENTICATOR"] = "SNOWFLAKE_JWT"
    os.environ["SNOWFLAKE_ACCOUNT"] = account
    os.environ["SNOWFLAKE_ROLE"] = role
    os.environ["SNOWFLAKE_WAREHOUSE"] = SNOWFLAKE_WAREHOUSE
    os.environ["SNOWFLAKE_DATABASE"] = database
    os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"] = key_path

    return {
        'account': account,
        'role': role,
        'database': database
    }

def run_deploy(project_path):
    os.chdir(project_path)

    print("🔧 Building project...")
    os.system("snow snowpark build --temporary-connection")

    print("🚀 Deploying project...")
    os.system("snow snowpark deploy --replace --temporary-connection")

# === Main execution ===
if len(sys.argv) < 4:
    print("Usage: python deploy_snowpark_apps.py <root_directory> <manifest_file> <target_env>")
    exit(1)

root_directory = sys.argv[1]
manifest_file = sys.argv[2]
target_env = sys.argv[3]  # e.g. "wheels_dev"

print(f"\n📦 Deploying Snowpark projects from manifest: {manifest_file}")
print(f"🌍 Target environment: {target_env}")

# Load secrets and configure env vars for Snow CLI
configure_snowflake_env_vars(target_env)

# Load manifest YAML
with open(manifest_file, 'r') as f:
    manifest = yaml.safe_load(f)

project_paths = manifest.get("projects", [])

if not project_paths:
    print("⚠️ No projects listed in manifest. Nothing to deploy.")
    exit(0)

for rel_path in sorted(set(project_paths)):
    full_path = os.path.join(root_directory, rel_path)
    print(f"\n📁 Processing project: {rel_path}")
    run_deploy(full_path)

print("\n✅ All deployments complete.")
