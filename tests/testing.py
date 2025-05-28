import os
import subprocess

# lines = []
# with open(os.path.expanduser("~/testing.txt"), "r") as outfile:
#     lines_ = outfile.readlines()
#     for line in lines_:
#         print(lines)
#         if (line == "\n"):
#             continue
#         if (line[:28] != "export AMADEUS_ACCESS_TOKEN="):
#             lines.append(line)
# with open(os.path.expanduser("~/testing.txt"), "w") as outfile:
#     outfile.writelines(lines)
#     outfile.write(f"\nexport AMADEUS_ACCESS_TOKEN='dude can  use'")
#     outfile.close()

subprocess.run("mkdir lmfoa", shell=True)