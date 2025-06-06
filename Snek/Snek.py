import socket
import time
import os
import threading
from ping3 import ping # type: ignore
from concurrent.futures import ThreadPoolExecutor
# import our PowerShell module PowerShellScripts class
from PowerShell.PowerShellScripts import PowerShellScripts

# lock objects
good_lock = threading.Lock()
fail_lock = threading.Lock()
user_lock = threading.Lock()

# computer lists
good_list: list[str] = []
fail_list: list[str] = []

# user dictionary
users: dict[str, str] = dict()

def _update_count(name: str, computer: str):
  # set our variables to the global scope
  global good_list
  global fail_list
  # get our count to update by name
  match name.lower():
    case "good":
      with good_lock:
        good_list.append(computer)
    case "fail":
      with fail_lock:
        fail_list.append(computer)
    case _:
      print(f"update_count: Unknown name '{name}'")

def _list_chunks(input_list: list[str], n: int):
  # yield successive n-sized chunks from lst
  for i in range(0, len(input_list), n):
    yield input_list[i:i + n]

def _ping_computer_chunk(computers: list[str]):
  for computer in computers:
    ping_result = ping(dest_addr=computer, timeout=1, unit="ms")
    if (ping_result == False or ping_result == None):
      # not found
      _update_count("fail", computer)
    else:
      if(ping_result > 0):
        try:
          result = socket.gethostbyaddr(computer)
          name = result[0].split('.')[0]
          if (computer.lower() != name.lower()):
            # dns mismatch
            _update_count("fail", computer)
          else:
            # good
            _update_count("good", computer)
        except socket.herror:
          # not found
          _update_count("fail", computer)
      else:
          # not found
          _update_count("fail", computer)

def ping_computers(computer_list: list[str]) -> None:
  # create our start time
  start_time = time.time()

  # get the number of CPUs our computer has
  cpu_count: int | None = os.cpu_count()
  # we will calculate our worker count based on our cpu count
  worker_count: int = 50
  # check if we received a cpu count
  if cpu_count != None:
    # set worker count to 10 times our cpu count
    worker_count = cpu_count * 10

  # create our thread pool
  with ThreadPoolExecutor(max_workers=worker_count) as executor:
    # execute our commands in threads
    executor.map(_ping_computer_chunk, _list_chunks(computer_list, 5))

  # create our end time after the work has been done
  end_time = time.time()
  # calculate our elapsed time
  elapsed_time = end_time - start_time

  # get our counts
  good_count = len(good_list)
  fail_count = len(fail_list)

  # print our results
  print(f"Computers: {len(computer_list)}")
  print(f"Time: {elapsed_time:.2f}s")
  per_second = len(computer_list) / elapsed_time
  print(f"Checked {per_second:.2f} computers/second")
  print(f"Good: {good_count}")
  print(f"Fail: {fail_count}")
  print(f"Total: {good_count + fail_count}")

def _get_user_chunks(computers: list[str]):
  for computer in computers:
    user: str = powershell_scripts.get_user(computer)
    #print(f"{computer}: {user}")
    with user_lock:
        users[computer] = user

def get_users(computer_list: list[str]):
  # create our start time
  start_time = time.time()

  # get the number of CPUs our computer has
  cpu_count: int | None = os.cpu_count()
  # we will calculate our worker count based on our cpu count
  worker_count: int = 50
  # check if we received a cpu count
  if cpu_count != None:
    # set worker count to 10 times our cpu count
    worker_count = cpu_count * 10

  # create our thread pool
  with ThreadPoolExecutor(max_workers=worker_count) as executor:
    # execute our commands in threads
    executor.map(_get_user_chunks, _list_chunks(computer_list, 5))

  # create our end time after the work has been done
  end_time = time.time()
  # calculate our elapsed time
  elapsed_time = end_time - start_time

  # write our users to a file
  with open("users.txt", "w") as f:
    # loop through our keys
    for key in users.keys():
      # change any connection warnings to errors
      if "WARNING" in users[key]:
        users[key] = "Error"
      # write the computer and user
      f.write(f"{key}: {users[key]}\n")

  # get some counts from our values
  values_list = list(users.values())
  error_count = values_list.count('Error')
  no_user_count = values_list.count('')
  user_count = len(values_list) - error_count - no_user_count

  # print our results
  print(f"Computers: {len(computer_list)}")
  print(f"Time: {elapsed_time:.2f}s")
  per_second = len(computer_list) / elapsed_time
  print(f"Checked {per_second:.2f} users/second")
  print(f"Errors: {error_count}")
  print(f"No User: {no_user_count}")
  print(f"User: {user_count}")

if __name__ == "__main__":
  # create our powershell script object
  powershell_scripts: PowerShellScripts = PowerShellScripts()

  # get our computer list from AD
  print("Getting computers from AD")
  ad_computers = powershell_scripts.get_ad_computers()

  # ping our computer and fill our good/fail lists
  print("\nPinging computers")
  ping_computers(ad_computers)

  # get the logged in user for each computer we could ping
  print("\nGetting logged in users")
  get_users(good_list)
  