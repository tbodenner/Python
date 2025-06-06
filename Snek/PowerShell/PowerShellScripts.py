import os
import subprocess

class PowerShellScripts:
  def __init__(self):
    # script folder name
    self.SCRIPT_FOLDER_NAME = 'Scripts'
    # script extension for powershell files
    self.SCRIPT_EXTENSION = '.ps1'
    # script folder
    self.script_folder = os.path.join(os.path.split(__file__)[0], self.SCRIPT_FOLDER_NAME)
    # powershell scripts
    self.powershell_scripts: dict[str, str] = dict()
    # fill our powershell script dictionary
    self._read_script_files_to_dict(self._get_all_script_files())
    # print our scripts
    print("Scripts:")
    for key in self.powershell_scripts.keys():
      print(f"  {key}")

  # read the contents of our script to our dictionary
  def _read_script_files_to_dict(self, file_paths: list[str]) -> None:
    # for each of our files
    for path in file_paths:
      # get the file name without an extension or root folder
      script_name = os.path.splitext(os.path.split(path)[1])[0]
      # check if the script is in our dictionary
      if script_name not in self.powershell_scripts:
        # load the script into our dictionary
        self.powershell_scripts[script_name] = self._read_script(path)

  # read all script files into our script dictionary
  def _get_all_script_files(self) -> list[str]:
    # our script files
    script_files: list[str] = list()
    # read our directory
    for path in os.listdir(self.script_folder):
      full_path: str = os.path.join(self.script_folder, path)
      # check if the item is a file
      if os.path.isfile(full_path) == True:
        # check if the file extension matches our script extension
        if os.path.splitext(full_path)[1] == self.SCRIPT_EXTENSION:
          # add the item path to our list
          script_files.append(full_path)
    # return our file list
    return script_files

  # read the contents of a script file
  def _read_script(self, file_name: str) -> str:
    # our script data
    output: str = ""
    # open the file for reading
    with open(file_name, "r") as f:
        # read the lines to our output
        output = f.read()
    # return our script data
    return output

  # run a powershell command as powershell version 5
  def run_powershell_5_command(self, command: str) -> str:
    return self._run_powershell_command(5, command)

  # run a powershell command as powershell version 7
  def run_powershell_7_command(self, command: str) -> str:
    return self._run_powershell_command(7, command)

  # run a powershell command
  def _run_powershell_command(self, version: int, command: str) -> str:
    powershell_process: str = ""
    # select our powershell executable by version
    match version:
        case 5:
            powershell_process = "powershell"
        case 7:
            powershell_process = "pwsh"
        case _:
            return ""
    # our arguments to pass to subprocess.run
    run_args = [powershell_process, "-ExecutionPolicy", "bypass", "-Command", command]
    # create and run our process
    process = subprocess.run(
      run_args, 
      capture_output=True, 
      text=True
    )
    # return the output of the powershell command
    return process.stdout.strip()

  # get a list of all scripts in our dictionary
  def get_script_names(self) -> list[str]:
    # return our keys as a list
    return list(self.powershell_scripts.keys())

  # run a script by name in our dictionary
  def run_script(self, script_name: str, script_args: list[str] = []) -> list[str]:
    if script_name not in self.powershell_scripts:
      # return a list with an error message
      return ['script not found']
    else:
      # otherwise, run the script
      return self.run_powershell_7_command(self.powershell_scripts[script_name]).split('\n')

  # run the script to get all computers in AD
  def get_ad_computers(self) -> list[str]:
      # script name
      SCRIPT_NAME = "Get-ComputerArray"
      # run the script
      return self.run_script(SCRIPT_NAME)

  def get_user(self, computer: str) -> str:
    # script name
    SCRIPT_NAME = "Get-LoggedInUser"
    # update our computer name in our script command string
    script_command: str = self.powershell_scripts[SCRIPT_NAME]
    script_command = script_command.replace("PYTHON_COMPUTERNAME", computer)
    # run the script
    return self.run_powershell_7_command(script_command).split('\n')[0]

# create the class object if run directly
if __name__ == "__main__":
  # create our powershell script object
  powershell_scripts: PowerShellScripts = PowerShellScripts()
