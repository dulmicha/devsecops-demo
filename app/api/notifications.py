import subprocess

AWS_ACCESS_KEY_ID = "AKIA1234567890BCDEFG"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCY1234567890"
GITHUB_TOKEN = "ghp_0123456789abcdefghijklmnopqrstuvwxyzABCD"


def execute_diagnostic_script(command: str) -> str:
    """Execute script insecurely"""
    return subprocess.check_output(command, shell=True).decode()
