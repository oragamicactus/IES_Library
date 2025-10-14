"""Cleanup temp files after rendering is completed, both duplicate maya scene and moves and renames thumbnail images."""

import sys, os

IESLibraryDirectory = sys.argv[1]
duplicateFile = sys.argv[2]
sourceFolder = sys.argv[3] or os.path.join(IESLibraryDirectory, "IES_images/Temp")
destinationFolder = sys.argv[4] or os.path.join(IESLibraryDirectory, "IES_images")
missingThumbnails = sys.argv[5].split(",")

# Ensure there are missing thumbnails to process
if missingThumbnails is None or missingThumbnails == []:
    sys.exit("No missing thumbnails")
# Ensure source folder exists
if not os.path.exists(sourceFolder):
    sys.exit("Invalid source path")
# Ensure destination folder exists
if not os.path.exists(destinationFolder):
    sys.exit("Invalid destincation path")

# Import send2trash module for moving to recycling bin
try:
    from send2trash import send2trash
except:
    s2tModule = f"{IESLibraryDirectory}\\".replace("/", "\\")
    sys.path.append(s2tModule)
    from send2trash import send2trash

normalizedPath = os.path.normpath(duplicateFile)

# Delete duplicate maya thumbnail scene
try:
    #print("Deleting temporary scene:", duplicateFile)
    send2trash(normalizedPath)
except FileNotFoundError:
    sys.exit()

# copy ies file list and remove .ies extension
nameList = [name.split(".")[0] for name in missingThumbnails]
nameList.reverse()  # reverse for easier pop() with less performance impact

unprocessedThumbnails = sorted(os.listdir(sourceFolder))

# Iterate through files in source folder
for filename in unprocessedThumbnails:
    if os.path.isfile(os.path.join(sourceFolder, filename)):
        new_filename = nameList.pop() + ".png"
        source_file = os.path.join(sourceFolder, filename)
        destination_file = os.path.join(destinationFolder, new_filename)

        # Rename and move file
        os.rename(source_file, destination_file)