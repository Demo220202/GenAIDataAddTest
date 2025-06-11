import subprocess
import sys
import time

def run_command(command):
    """Run a shell command and print its output or error."""
    try:
        print(f"\nExecuting: {command}")
        result = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {e.cmd}")
        print(e.stderr)

if __name__ == "__main__":
    # Delete the Cognitive Services accounts
    run_command("az cognitiveservices account delete -n test001 -g test")
    run_command("az cognitiveservices account delete -n prediction-resource002 -g test")

    # Optional: Wait for a few seconds if needed for soft-delete to register
    time.sleep(30)

    # Purge the soft-deleted Cognitive Services accounts
    run_command("az cognitiveservices account purge --name test001 -g test --location westus")
    run_command("az cognitiveservices account purge --name prediction-resource002 -g test --location westus")

