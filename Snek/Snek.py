import socket
import time
import os
import re
import threading
import sqlite3
from datetime import datetime
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

# sqlite file for our user logged in times
users_logged_in_db = 'users.db'

# user dictionary
users: dict[str, tuple[str, datetime]] = dict()

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
        users[computer] = (user, datetime.now())

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

  # create our file name for our output file
  file_name = "Users." + datetime.now().strftime('%Y%m%d%H%M%S') + ".txt"
  # list of our user data
  all_user_data: list[list[str]] = []
  # write our users to a file
  with open(file_name, "w") as f:
    # loop through our keys
    for key in users.keys():
      # change any connection warnings to errors
      if "WARNING" in users[key][0]:
        users[key] = ("Error", datetime.now())
      # write the computer and user
      f.write(f"{key}, {users[key][0]}, {users[key][1].strftime('%Y-%m-%d %H:%M:%S')}\n")
      # create a list of our user data
      user_data = [key.strip(), users[key][0].strip(), users[key][1].strftime('%Y-%m-%d %H:%M:%S').strip()]
      # add the list to our main list
      all_user_data.append(user_data)

  insert_into_sqlite(all_user_data)

  # get some counts from our values
  values_list = list(users.values())
  error_count = [user[0] for user in values_list].count('Error')
  no_user_count = [user[0] for user in values_list].count('')
  user_count = len(values_list) - error_count - no_user_count

  # print our results
  print(f"Computers: {len(computer_list)}")
  print(f"Time: {elapsed_time:.2f}s")
  per_second = len(computer_list) / elapsed_time
  print(f"Checked {per_second:.2f} users/second")
  print(f"Errors: {error_count}")
  print(f"No User: {no_user_count}")
  print(f"User: {user_count}")

def get_all_user_files(path: str) -> list[str]:
  # our regex to search for
  file_pattern = re.compile(r'Users\.[0-9]{14}\.txt')
  # get the full path for our input
  full_path = os.path.abspath(path)
  # get the files in our path that match our regex
  files = [f for f in os.listdir(full_path) if file_pattern.match(f)]
  # add our full path to the files and return them
  return [os.path.join(full_path, f) for f in files]

def get_user_data_from_file(file_name: str) -> list[str]:
  # our file contents
  file_contents = None
  # open the file in read mode
  with open(file_name, 'r') as f:
    # read the file contents
    file_contents = f.readlines()
  # return the list of lines
  return file_contents

def insert_into_sqlite(input_list: list[list[str]]) -> None:
  # create our connection string
  connection = sqlite3.connect(users_logged_in_db)
  # get our cursor
  cursor = connection.cursor()
  # create our table if it is not found
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS UserLogin (
        Computer TEXT NOT NULL,
        UserName TEXT NOT NULL,
        TimeStamp TEXT NOT NULL,
        PRIMARY KEY (Computer, UserName, TimeStamp)
    )
    """)
  # insert our list into the table
  cursor.executemany("INSERT OR REPLACE INTO UserLogin (Computer, UserName, TimeStamp) VALUES (?, ?, ?)", input_list)
  # commit the changes
  connection.commit()
  # close our connection
  connection.close()

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
  
  #file_content: list[list[str]] = []
  #files = get_all_user_files(os.path.dirname(__file__))
  #for file_name in files:
  #  file_data = get_user_data_from_file(file_name)
  #  for line in file_data:
  #    split_line = line.split(',')
  #    clean_line = [l.strip() for l in split_line]
  #    file_content.append(clean_line)
  #insert_into_sqlite(file_content)
