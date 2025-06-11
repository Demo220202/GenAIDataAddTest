import os
import shutil
from datetime import datetime

main_domain = "beta.zenarate.com"

# Paths
sites_dir = "/etc/nginx/sites-enabled/"
main_file = f"{main_domain}.conf"
path = os.path.join(sites_dir, main_file)
backup_dir = f"/home/ubuntu/nginxchanges/backup_{datetime.today().strftime('%Y-%m-%d')}"

# Check if beta file exists
if not os.path.exists(path):
    raise FileNotFoundError(f"{path} does not exist. Aborting...")

# Create backup directory
os.makedirs(backup_dir, exist_ok=True)

# Backup all .conf files
for filename in os.listdir(sites_dir):
    if filename.endswith(".conf"):
        shutil.copy2(os.path.join(sites_dir, filename), os.path.join(backup_dir, filename))

# Read beta file content
with open(path, 'r') as f:
    content = f.read()

# Process other files
for filename in os.listdir(sites_dir):
    if filename.endswith(".com.conf") and filename != main_file:
        domain = filename.replace(".conf", "")
        new_content = content.replace(main_domain, domain)

        target_path = os.path.join(sites_dir, filename)
        print(f"Replacing {filename} with updated content for domain {domain}")
        os.remove(target_path)
        with open(target_path, 'w') as f:
            f.write(new_content)