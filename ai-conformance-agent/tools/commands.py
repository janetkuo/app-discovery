import subprocess

def run_shell_command(command: str) -> dict:
  """
  Executes a shell command and returns its output, error, and exit code.

  Args:
    command (str): The shell command to execute.

  Returns:
    A dictionary containing the stdout, stderr, and exit_code.
  """
  print(f"--- Tool: Executing command: {command} ---")
  try:
    result = subprocess.run(
      command,
      shell=True,
      capture_output=True,
      text=True,
      check=False, # Set to False to not raise exception on non-zero exit codes
      timeout=60
    )
    return {
      "stdout": result.stdout,
      "stderr": result.stderr,
      "exit_code": result.returncode,
    }
  except Exception as e:
    return {"stdout": "", "stderr": str(e), "exit_code": 1}