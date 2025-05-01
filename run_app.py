import subprocess
import os
 
# Assuming CDSW_APP_PORT is set in the environment, otherwise default to a specific port
port = os.getenv('CDSW_READONLY_PORT', None)

# Construct the command
command = [
    "poetry","run",
    "streamlit", "run", "/home/cdsw/app_home.py", #"/home/cdsw/app_home.py",
    "--server.port", port,
    "--server.address", "127.0.0.1",
    "--server.headless", "true",
    "--global.developmentMode", "false",
    "--browser.gatherUsageStats", "false"
]
print(f"read-only-{os.getenv('CDSW_ENGINE_ID')}.{os.getenv('CDSW_DOMAIN')}")
# Run the command
subprocess.run(command)


