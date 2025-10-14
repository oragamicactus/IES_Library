"""
IES Library tool - V 1.0

This allows you to manage a list of IES files and easily apply them to your lights.
Also included is a thumbnail generator which will build thumbnails to match the
ies files.

Author: Graham Connell
"""

import os
import subprocess
import platform
import sys

import maya.cmds as cmds

# Global variables
UI_selectedProfileLabel = ""
UI_selectedProfileImage = "help.png"
missingThumbnails = []

# Local folder location
IESLibraryDirectory = "/Users/grahamconnell/Downloads/IES_Library" # Sets folder for IES library tool

# Load Arnold and Reshift plugins if not already loaded
arnoldNotAvailable = False
if not cmds.pluginInfo("mtoa", query=True, loaded=True):
    try:
        cmds.loadPlugin('mtoa')
    except:
        arnoldNotAvailable = True
if not cmds.pluginInfo("redshift4maya", query=True, loaded=True):
    try:
        cmds.loadPlugin('redshift4maya')
    except:
        if arnoldNotAvailable:
            cmds.warning("Cannot use IES Library without Arnold or Redshift. Please load 1 or both plugins and try again.")
            cmds.promptDialog("Neither Arnold nor Redhsift are available.\nPlease ensure 1 or both are available.")
            sys.exit()
        pass


# ------------------------------------------------------------------------
# Start functions

def createIESWindow() -> None:
    """Creates tool's only window where all functions and UI is stored."""

    IESwindowName = "IES Profile library"
    global UI_cardLayout, IESCardList

    if cmds.workspaceControl(IESwindowName, query=True, exists=True):
        cmds.deleteUI(IESwindowName)

    # Initialize window
    cmds.workspaceControl(IESwindowName, minimumWidth=514)
    UI_mainLayout = cmds.formLayout(numberOfDivisions=12, margins=8)

    UI_actionShelf = cmds.rowColumnLayout(numberOfRows=1)
    UI_openHelp = cmds.iconTextButton(
        style="iconOnly",
        image="help_line_NC.png",
        command=lambda *args: openHelpDocumentation(),
        annotation="Help documentation",
    )
    # UI_generateThumbnailsButton = cmds.button(label="Generate thumbnails", command=lambda *args: generateThumbnails(), annotation="Generate missing thumbnails")
    UI_openLibraryLocation = cmds.iconTextButton(
        style="iconOnly",
        image="folder-open.png",
        annotation="Open library folder",
        command=lambda *args: openLibraryDirectory(),
    )
    UI_generateThumbnailsButton = cmds.iconTextButton(
        style="iconOnly",
        image="imageDisplay.png",
        annotation="Generate missing thumbnails",
        command=lambda *args: generateThumbnails(),
    )

    cmds.setParent(UI_mainLayout)

    UI_primaryLayout = cmds.rowColumnLayout(adjustableColumn=True, numberOfColumns=2)
    UI_thumbnailLayout = cmds.scrollLayout(
        parent=UI_mainLayout, backgroundColor=(0.17, 0.17, 0.17)
    )

    # IES profile cards
    IESfiles = IESFileList()
    UI_cardLayout = cmds.rowColumnLayout(numberOfColumns=3)
    IESCardList = []
    # Build each card based on the ies files in the folder
    for IESfile in IESfiles:
        IESCardList.append(createCardUI(IESfile))

    # Current selection preview
    cmds.setParent(UI_primaryLayout)
    UI_columnRight = cmds.rowColumnLayout(numberOfColumns=1, parent=UI_mainLayout)
    cmds.text("Selected profile", font="boldLabelFont", align="left")
    selectedIESProfile = IESFileList()[0]
    global UI_selectedProfileLabel
    UI_selectedProfileLabel = cmds.text(
        f"{selectedIESProfile}", align="left", wordWrap=True
    )
    cmds.separator(height=4, width=1, visible=False)
    global UI_selectedProfileImage
    firstImage = selectedIESProfile.split(".")[0] or "help"
    UI_selectedProfileImage = cmds.iconTextStaticLabel(
        image=f"{IESLibraryDirectory}/IES_images/{firstImage}.png",
        style="iconOnly",
        width=256,
        height=256,
        parent=UI_columnRight,
    )

    cmds.setParent(UI_mainLayout)
    UI_numberColumns = cmds.intSliderGrp(label="Columns: 1", width=240,value=3, min=1, max=6, extraLabel=" 6", cc=lambda *args: editThumbnailColumns(UI_thumbnailLayout, UI_thumbnailLayout,UI_numberColumns, UI_cardLayout))
    # Build UI for compatible lights
    cmds.separator(height=8, width=1, visible=False)
    cmds.text(
        "Compatible IES lights",
        font="boldLabelFont",
        align="left",
        parent=UI_columnRight,
    )
    cmds.separator(height=4, width=1, visible=False)
    IESLightList = compatibleLightList()
    UI_IESLightList = cmds.textScrollList(
        allowMultiSelection=True, parent=UI_mainLayout
    )
    buildCompatibleLightList(IESLightList, UI_IESLightList)

    # Subscribe to DAG objects being created
    # When a new DAG object appears, check that it's an
    # IES light and build the new list
    # Jobs automatically killed when the parent window is closed
    lightJobs = []
    lightJobs.append(
        cmds.scriptJob(
            event=[
                "DagObjectCreated",
                lambda: checkForNewLights(IESLightList, UI_IESLightList),
            ],
            parent=IESwindowName,
        )
    )
    # Used to detect when light is deleted
    lightJobs.append(
        cmds.scriptJob(
            event=[
                "SelectionChanged",
                lambda: selectionChanged(IESLightList, UI_IESLightList),
            ],
            parent=IESwindowName,
        )
    )
    lightJobs.append(
        cmds.scriptJob(
            event=[
                "SelectionChanged",
                lambda: selectionChanged(IESLightList, UI_IESLightList),
            ],
            parent=IESwindowName,
        )
    )

    cmds.setParent(UI_mainLayout)
    UI_lightButtons = cmds.rowLayout(numberOfColumns=3)
    UIButton_createLight = cmds.button(
        label="Create light", command=lambda *args: createLight()
    )
    cmds.separator(height=1, width=4, visible=False)
    UIbutton_applyProfileToLight = cmds.button(
        label="Apply to selected lights >",
        command=lambda *args: applyProfileToLight(UI_IESLightList),
    )

    cmds.setParent(IESwindowName)
    # Layout UI within UI_mainLayout
    cmds.formLayout(
        UI_mainLayout,
        edit=True,
        attachForm=[
            (UI_actionShelf, "bottom", 4),
            (UI_actionShelf, "left", 8),
            (UI_lightButtons, "right", 8),
            (UI_lightButtons, "bottom", 4),
            (UI_columnRight, "right", 8),
            (UI_columnRight, "top", 8),
            (UI_thumbnailLayout, "top", 8),
            (UI_thumbnailLayout, "left", 8),
            (UI_IESLightList, "right", 0),
            (UI_numberColumns, "bottom", 8)
        ],
        attachNone=[(UI_actionShelf, "right")],
        attachControl=[
            (UI_thumbnailLayout, "bottom", 8, UI_actionShelf),
            (UI_thumbnailLayout, "right", 8, UI_columnRight),
            (UI_columnRight, "bottom", 8, UI_primaryLayout),
            (UI_IESLightList, "left", 8, UI_thumbnailLayout),
            (UI_IESLightList, "bottom", 8, UI_lightButtons),
            (UI_IESLightList, "top", 0, UI_columnRight),
            (UI_numberColumns, "right", 8, UI_IESLightList)
        ],
    )
    cmds.showWindow(IESwindowName)


def editThumbnailColumns(parentLayout, cardList, UI_columns, UI_thumbnails) -> None:
    columns = cmds.intSliderGrp(UI_columns, query=True, value=True)

    cmds.deleteUI(UI_thumbnails)
    global UI_cardLayout, IESCardList
    UI_cardLayout, IESCardList = createThumbnailUI(parentLayout, columns=columns)


def createThumbnailUI(parentLayout, columns=3):
    # IES profile cards
    IESfiles = IESFileList()
    UI_cardLayout = cmds.rowColumnLayout(numberOfColumns=columns, parent=parentLayout)
    IESCardList = []
    # Build each card based on the ies files in the folder
    for IESfile in IESfiles:
        IESCardList.append(createCardUI(IESfile))
    
    #cmds.formLayout(formLayout, edit=True, attachForm=(UI_cardLayout, "bottom", 24))

    return UI_cardLayout, IESCardList


def openHelpDocumentation() -> None:
    """Opens help documentation for this IES Library"""
    helpDocument = os.path.join(IESLibraryDirectory, "README.pdf")
    # Determine the current operating system
    current_platform = platform.system()

    # Use the appropriate command for each OS
    if current_platform == "Windows":
        os.startfile(helpDocument)
    elif current_platform == "Darwin":  # macOS
        os.system(f'open "{helpDocument}"')
    else:  # Assume Linux or other UNIX-like OS
        os.system(f'xdg-open "{helpDocument}"')


def openLibraryDirectory() -> None:
    """Opens IES library directory in the native system file dialog"""
    # Determine the current operating system
    current_platform = platform.system()

    # Use the appropriate command for each OS
    if current_platform == "Windows":
        os.startfile(IESLibraryDirectory)
    elif current_platform == "Darwin":  # macOS
        os.system(f'open "{IESLibraryDirectory}"')
    else:  # Assume Linux or other UNIX-like OS
        os.system(f'xdg-open "{IESLibraryDirectory}"')


def duplicateThumbnailScene(newSceneName="/IESMakeThumbnails1.ma"):
    """Duplicates the hidden IESMakeThumbnails.ma scene with given
    name. IESMakeThumbnails1 is the default for the new scene."""
    with open(IESLibraryDirectory + "/IESMakeThumbnails.ma", "r") as src_file:
        with open(IESLibraryDirectory + newSceneName, "w") as dest_file:
            dest_file.write(src_file.read())


def generateThumbnails() -> None:
    """Asks user how they want to generate missing thumbnail images, then starts the process to complete the renders, or builds the scene if 'Manual' option is selected"""

    # Catch if missingThumbnails list is empty, stop function if yes
    if len(missingThumbnails) <= 0:
        cmds.warning("No lights are missing images.")
        cmds.confirmDialog(
            message="No missing thumbnails, this feature only works on ies files with no image with a matching name.",
            button=["Ok"],
            cancelButton="Ok",
        )
        return

    # Get decision from user about render engine to use
    popupGenerate = cmds.confirmDialog(
        title="Generate thumbnails",
        message="Creates thumbnails for any ies file that is missing one.\n\nThe background process can take several minutes, you'll see a popup once the operation is complete.\n\nSee README for more help with this function.",
        icon="question",
        button=["Cancel", "Manual", "Redshift", "Arnold"],
        cancelButton="Cancel",
        defaultButton="Arnold",
        dismissString="Aborted thumbnail generation",
    )
    match popupGenerate:
        case "Cancel":
            return
        case "Manual":
            duplicateThumbnailScene("/IESMakeThumbnailsManual.ma")

            # Create batch file
            batchFile = createBatFile(
                buildScene=True, renderScene=False, renderEngine="both"
            )
            if batchFile == "didn't work":
                cmds.warning("Error creating thumbnail batch file. Aborted process.")

            # Warn user this could take a bit
            UI_thumbnailWarning = cmds.confirmDialog(
                title="Thumbnail scene generation",
                message="This process can take several moments, Maya is frozen during this time. Your current scene will remain open.\n\nYou'll see a message once the process has finished",
                b=["Cancel", "Continue"],
                cancelButton="Cancel",
                defaultButton="Continue",
            )
            if UI_thumbnailWarning == "Cancel":
                return

            # Build scene and render
            cmds.warning(
                "Building thumbnails in background, this will take a few moments"
            )
            executeBatFile(batchFile)
            subprocess.run(["attrib", "+h", batchFile], shell=True)

            cmds.confirmDialog(
                title="Scene created",
                message="Thumbnail scene has been built! You'll find the scene in the IES_Library with the name 'IESMakeThumbnailsManual.ma'",
                b=["Ok"],
                cancelButton="Ok",
                defaultButton="Ok",
            )
        case "Arnold":
            # Create a duplicate of thumbnail scene
            duplicateThumbnailScene()

            # Create batch file
            batchFile = createBatFile(
                buildScene=True, renderScene=True, renderEngine="arnold"
            )
            if batchFile == "didn't work":
                cmds.warning("Error creating thumbnail batch file. Aborted process.")
                return

            # Warn user this could take a bit
            UI_thumbnailWarning = cmds.confirmDialog(
                title="Arnold thumbnail generation",
                message="This process can take several minutes. You may continue to use Maya, rendering will be done in the background.",
                b=["Cancel", "Continue"],
                cancelButton="Cancel",
                defaultButton="Continue",
            )
            if UI_thumbnailWarning == "Cancel":
                return

            # Build scene and render
            cmds.warning(
                "Rendering thumbnails in background, this will take a few moments"
            )
            executeBatFile(batchFile)
            process = subprocess.Popen(["attrib", "+h", batchFile], shell=True) # hides bat file in explorer

        case "Redshift":
            # Create a duplicate of thumbnail scene
            duplicateThumbnailScene()

            

            # Create batch file
            batchFile = createBatFile(
                buildScene=True, renderScene=True, renderEngine="redshift"
            )
            if batchFile == "didn't work":
                cmds.warning("Error creating thumbnail batch file. Aborted process.")
                return

            # Warn user this could take a bit, the
            UI_thumbnailWarning = cmds.confirmDialog(
                title="Redshift thumbnail generation",
                message="This process can take several minutes, Maya is frozen during this time. Your current scene will remain open.\n\nYou'll see a message once the process has finished",
                b=["Cancel", "Continue"],
                cancelButton="Cancel",
                defaultButton="Continue",
            )
            if UI_thumbnailWarning == "Cancel":
                return

            # Build scene and render
            cmds.warning(
                "Building thumbnails in background, this will take a few moments"
            )
            executeBatFile(batchFile)
            process = subprocess.Popen(["attrib", "+h", batchFile], shell=True)

        case _:
            pass


def windowsNotification() -> str:
    command = "python " + os.path.join(IESLibraryDirectory, "windowsNotification.py")

    return command


def createBatFile(buildScene=False, renderScene=False, renderEngine="arnold") -> str:
    """Creates .bat file with a command to build the thumbnail scene, and render the scene (both optional)."""

    if not buildScene and not renderScene:
        return "didn't work"
    
    if buildScene:
        generateScenePrompt = buildGenerateScene(
            missingThumbnails, IESLibraryDirectory, renderer=renderEngine
        )
    if renderScene:
        renderScene = backgroundRender(
            missingThumbnails, IESLibraryDirectory, renderEngine
        )
        cleanupScene = thumbnailCleanup()
    if generateScenePrompt is None or renderScene is None:
        return "didn't work"

    batFilePath = os.path.join(IESLibraryDirectory, "batchProcess.bat")

    if os.path.isfile(batFilePath):
        subprocess.run(["attrib", "-h", batFilePath], shell=True)

    with open(batFilePath, "w+") as batFile:
        if buildScene:
            batFile.write(generateScenePrompt + "\n")
        if renderScene:
            batFile.write(renderScene + "\n")
            batFile.write(cleanupScene + "\n")
            if platform.system() == "Windows":
                batFile.write(windowsNotification())

    return batFilePath


def executeBatFile(batFilePath: str = None) -> None:
    """Executes the provided .bat file."""

    if batFilePath is None or not os.path.isfile(batFilePath):
        return
    assert batFilePath.split(".")[-1] == "bat", "File must be .bat"

    process = subprocess.Popen([batFilePath], shell=True)
    return


def buildGenerateScene(
    missingThumbnailList,
    libraryDirectory,
    renderFrames=True,
    renderer="arnold",
    newScenePath="/IESMakeThumbnails1.ma",
) -> str:
    """Builds new scene to generate thumbnails from using the selected
    renderer (arnold or redshift). Also works with 'both' command to build
    a scene that has the profiles and lights for both renderers.
    Returns a string that can be run through the subprocess module or saved to a .bat file
    """
    missingThumbnailString = commaSeparatedList(missingThumbnailList)
    # Validate data
    if len(missingThumbnailList) == 0:
        print("List of missing thumbnails is empty")
        return
    if not libraryDirectory and not os.path.isdir(libraryDirectory):
        print("Directory: " + str(os.path.isdir(libraryDirectory)))
        return
    # Validate render engine and ensure it's in acceptable case
    match renderer:
        case "arnold" | "Arnold":
            renderer = "arnold"
        case "redshift" | "Redshift":
            renderer = "redshift"
        case "both" | "Both":
            renderer = "both"
        case _:
            print(f"{renderer} is not a valid engine")
            return

    maya_version = cmds.about(version=True)  # Year version of maya
    env = os.environ.copy()

    mayapyPath = f"C:/Program files/Autodesk/Maya{maya_version}/bin/mayapy.exe"

    # Ensure mayapy is in expected location
    if not os.path.isfile(mayapyPath):
        cmds.confirmDialog(
            message="mayapy not found at common installation location.\n\nPlease select the location of mayapy (usually in the /Autodesk/MayaXXXX/bin directory)"
        )
        mayapyPath = cmds.fileDialog2()
        if not os.path.isfile(mayapyPath) or "mayapy.exe" not in mayapyPath:
            cmds.warning("Not a valid path for mayapy.exe")
            return None

    command = f'"{mayapyPath}" {libraryDirectory}/IESmayaSceneSetup.py {missingThumbnailString} {libraryDirectory} {renderer} {renderFrames} {newScenePath}'

    return command
    # process = subprocess.Popen(command, env=env, shell=True, stdout=subprocess.PIPE) #,
    # process.wait()
    # return process


def backgroundRender(
    missingThumbnailList, libraryDirectory, renderer="arnold", camera="renderCam"
) -> str:
    """Builds command to start a subprocess to render a thumbnail scene.
    Returns a string that can be directly ran, or saved to a .bat file."""

    if libraryDirectory:
        imageDirectory = libraryDirectory + "/IES_images/Temp/"
    # Validate data
    if len(missingThumbnailList) == 0:
        print("List of missing thumbnails is empty")
        return
    if not imageDirectory and not os.path.isdir(imageDirectory):
        print("Directory: " + str(os.path.isdir(imageDirectory)))
        return
    # Validate render engine and ensure it's in acceptable case
    match renderer:
        case "arnold" | "Arnold":
            renderer = "arnold"
        case "redshift" | "Redshift":
            renderer = "redshift"
        case _:
            print(f"{renderer} is not a valid engine")
            return None

    maya_version = cmds.about(version=True)  # Year version of maya
    endFrame = len(missingThumbnailList)
    env = os.environ.copy()

    renderEXE = f"C:/Program Files/Autodesk/Maya{maya_version}/bin/Render.exe"

    # Ensure mayapy is in expected location
    if not os.path.isfile(renderEXE):
        cmds.confirmDialog(
            message="Render.exe not found at common installation location.\n\nPlease select the location of Render.exe (usually in the /Autodesk/MayaXXXX/bin directory)"
        )
        renderEXE = cmds.fileDialog2()
        if not os.path.isfile(renderEXE) or "Render.exe" not in renderEXE:
            cmds.warning("Not a valid path for mayapy.exe")
            return None

    renderPrompt = f'"{renderEXE}" -r {renderer} -cam {camera} -s 1 -e {endFrame} -rd "{imageDirectory}" {libraryDirectory}/IESMakeThumbnails1.ma'

    return renderPrompt


def thumbnailCleanup(
    duplicateFile=IESLibraryDirectory + "/IESMakeThumbnails1.ma",
    sourceFolder=IESLibraryDirectory + "/IES_images/Temp",
    destinationFolder=IESLibraryDirectory + "/IES_images",
) -> str:
    """Builds subprocess command to run cleanup script (used in bat file)"""
    iesFileNames = commaSeparatedList(missingThumbnails)

    command = f'python {IESLibraryDirectory}/cleanupFiles.py {IESLibraryDirectory} {duplicateFile} {sourceFolder} {destinationFolder} {iesFileNames}'

    return command


def clearDirectory(path: str) -> None:
    """Checks if the directory at 'path' is empty. If it is not empty,
    deletes all files and subdirectories within it.
    """
    try:
        from send2trash import send2trash
    except:
        s2tModule = f"{IESLibraryDirectory}\\".replace("/", "\\")
        sys.path.append(s2tModule)
        from send2trash import send2trash

    if not os.path.isdir(path):
        raise ValueError(f"The path '{path}' is not a valid directory.")

    # List all entries in the directory
    entries = os.listdir(path)
    print(entries)

    if entries:
        # The directory is not empty, so delete all its contents
        for entry in entries:
            filePath = os.path.join(path, entry)
            normalizedPath = os.path.normpath(filePath)

            send2trash(normalizedPath)
        print(f"All temporary contents of the directory '{path}' have been deleted.")
    else:
        pass


def commaSeparatedList(currentList) -> str:
    """Converts list into a comma-separated string"""
    listString = ""
    for item in currentList:
        listString += str(item) + ","
    return listString[0:-1]


def selectionChanged(IESLightList: list, UI_LightList):
    """Checks for new lights in the scene, updates window light selection to match scene."""

    # Check and build new light list in case it has changed
    checkForNewLights(IESLightList, UI_LightList)

    # Match selection in compatible light list
    selectList = cmds.ls(selection=True)
    selectedIESLights = checkSelectionForIESLight(selectList)

    if selectedIESLights is None or selectedIESLights == []:
        cmds.textScrollList(UI_LightList, edit=True, deselectAll=True)
        return
    if len(selectedIESLights) != 0:
        cmds.textScrollList(UI_LightList, edit=True, deselectAll=True)
        for light in selectedIESLights:
            cmds.textScrollList(UI_LightList, edit=True, selectItem=light)


def nodeIsAiOrRsLight(selectedNode) -> bool:
    """Checks if the provided node is an Arnold photometric light or Redshift IES light."""

    if not cmds.objExists(selectedNode):
        return False
    
    try:
        nodeType = cmds.nodeType(selectedNode)
    except RuntimeError:
        return False
    
    if nodeType in ("aiPhotometricLight", "RedshiftIESLight"):
        return True
    return False


def checkSelectionForIESLight(selectList: list) -> list:
    """Accepts list of selected objects and returns list of IES compatible lights."""
    if cmds.listRelatives(selectList, allDescendents=True) is not None:
        selectList = selectList + cmds.listRelatives(selectList, allDescendents=True)
    selectedIESLights = []
    if selectList is None or len(selectList) <= 0:
        return

    for selectedItem in selectList:
        # Strip leading | for namespaces
        if selectedItem[0] == "|":
            selectedItem = selectedItem[1:]
        if nodeIsAiOrRsLight(selectedItem):
            selectedIESLights.append(selectedItem)
        else:
            #Handles namespace cases
            longName = cmds.ls(selectedItem, long=True)[0][1:]
            if nodeIsAiOrRsLight(longName):
                selectedIESLights.append(longName)


    return selectedIESLights


def applyProfileToLight(UI_lightList, *pArgs) -> None:
    """Handles button press for applying profile to light(s)"""
    global selectedIESProfile
    selectedProfile = selectedIESProfile
    lightList = cmds.textScrollList(UI_lightList, query=True, selectItem=True)
    if lightList is None:
        cmds.warning(
            "No compatible lights selected, use list or select compatible lights in"
        )
        return

    for light in lightList:
        lightType = cmds.objectType(light)
        match lightType:
            case "aiPhotometricLight":
                applyProfileArnold(selectedProfile, light)
            case "RedshiftIESLight":
                applyProfileRedshift(selectedProfile, light)


def applyProfileArnold(IESprofile, arnoldLight) -> None:
    """Sets IES profile for given Arnold light"""
    IESprofilePath = IESLibraryDirectory + "/IES_files/" + IESprofile
    cmds.setAttr(arnoldLight + ".aiFilename", IESprofilePath, type="string")


def applyProfileRedshift(IESprofile, redshiftLight) -> None:
    """Sets IES profile for given Redshift light"""
    IESprofilePath = IESLibraryDirectory + "/IES_files/" + IESprofile
    cmds.setAttr(redshiftLight + ".profile", IESprofilePath, type="string")


def buildCompatibleLightList(IESLightList, UI_LightList) -> None:
    """Rebuilds compatible light list, removing all old lights and adding new lights
    in the process."""

    if UI_LightList:
        cmds.textScrollList(UI_LightList, edit=True, removeAll=True)

    for IESLight in IESLightList:
        cmds.textScrollList(UI_LightList, edit=True, append=IESLight)


def createCardUI(IESfile, cardSize=128) -> str:
    """Creates UI card for IES light and returns the cmds UI compenent as a string"""

    profileName = IESfile.split(".")[0]
    profileImagePath = IESImageFilePath(profileName)

    # Add to missing list to generate missing images
    if profileImagePath == IESLibraryDirectory + "/IES_images/help.png":
        global missingThumbnails
        missingThumbnails.append(profileName)

    UI_card = cmds.rowLayout()

    UI_cardImage = cmds.iconTextButton(
        highlightColor=(0.5, 0.5, 0.5),
        scaleIcon=True,
        width=cardSize,
        height=cardSize + 16,
        style="iconAndTextVertical",
        image1=profileImagePath,
        label=profileName,
        command=lambda: selectIESProfile(IESfile),
    )
    cmds.setParent("..")

    return UI_cardImage


def selectIESProfile(IESProfile) -> None:
    """Sets globabl variables for selected profile. Updates selected profile thumbnail in UI"""
    global selectedIESProfile
    global UI_selectedProfileLabel
    global UI_selectedProfileImage

    profileImage = IESImageFilePath(IESProfile.split(".")[0])

    cmds.iconTextStaticLabel(UI_selectedProfileImage, edit=True, image=profileImage)
    cmds.text(UI_selectedProfileLabel, edit=True, label=IESProfile)
    selectedIESProfile = IESProfile


def IESImageFilePath(IESProfileName) -> str:
    """Builds profile path and return it if valid, returns default '?' image if not."""
    profilePath = IESLibraryDirectory + "/IES_images/" + IESProfileName + ".png"
    if validPath(profilePath, True):
        return profilePath
    else:
        return IESLibraryDirectory + "/IES_images/help.png"


def getCurrentRenderer() -> str:
    """Gets the current renderer. Offers to change to Arnold or Redshift if either is not currently selected."""
    currentRenderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")

    # Check if the renderer is Redshift or Arnold
    # If not, offer to change to either renderer
    if currentRenderer == "redshift" or currentRenderer == "arnold":
        return currentRenderer
    else:
        errorMessage = cmds.confirmDialog(
            title="Renderer not supported",
            message=f"{currentRenderer} isn't supported with this tool. Would you like to switch to Redshift or Arnold?",
            button=["Arnold", "Redshift", "Cancel"],
        )
        match errorMessage:
            case "Arnold":
                cmds.setAttr(
                    "defaultRenderGlobals.currentRenderer", "arnold", type="string"
                )
                currentRenderer = "arnold"
            case "Redshift":
                cmds.setAttr(
                    "defaultRenderGlobals.currentRenderer", "redshift", type="string"
                )
                currentRenderer = "redshift"
            case _:
                pass
        return currentRenderer


def IESFileList() -> list:
    """Return list of IES files to use in library"""

    IESLibraryList = cmds.getFileList(
        filespec="*.ies", folder=IESLibraryDirectory + "/IES_files"
    )
    return IESLibraryList


def createLight() -> None:
    match getCurrentRenderer():
        case "arnold":
            transform_node = cmds.createNode("transform", name="aiPhotometricLight#")
            newLight = cmds.shadingNode(
                "aiPhotometricLight",
                asLight=True,
                name="rsIESLightShape#",
                parent=transform_node,
            )

            applyProfileArnold(selectedIESProfile, newLight)
        case "redshift":
            transform_node = cmds.createNode("transform", name="rsIESLight#")
            newLight = cmds.shadingNode(
                "RedshiftIESLight",
                asLight=True,
                name="rsIESLightShape#",
                parent=transform_node,
            )
            cmds.setAttr(f"{newLight}.rx", -90)  # Set to face down

            applyProfileRedshift(selectedIESProfile, newLight)


def compatibleLightList() -> list:
    """Returns a list of IES compatible lights in the scene. If none, returns a list with ["No compatible lights"]."""

    lightList = cmds.ls(type=("aiPhotometricLight", "RedshiftIESLight"))
    if lightList == []:
        return ["No compatible lights"]
    return lightList


def checkForNewLights(existingLights, UI_IESLights) -> None:
    """Verifies if there are new lights not already in compatible light list.
    Rebuilds light list if there are including all compatible lights."""

    newLights = compatibleLightList()

    if existingLights != newLights:
        buildCompatibleLightList(newLights, UI_IESLights)


def validPath(path, checkFile=False) -> bool:
    """Checks if a path is valid and exists, returns True or False."""
    if os.path.exists(path):
        if os.path.isfile(path):
            return True
        elif not checkFile and os.path.isdir(path):
            return True
        else:
            return True
    else:
        return False


def fileStringMatch(
    inputString: str, match1='IESLibraryDirectory', match2 = 'Sets folder for IES library tool'
) -> bool:
    """Checks if the provided string matches the pattern custom file path line"""
    IESLibraryDirectory = ""  # Sets folder for IES library tool
    if match1 in inputString and match2 in inputString:
        return True
    return False


def checkIESDirectory() -> None:
    """Checks global variable IESLibraryDirectory to ensure it's a valid path, checks common installation locations, asks user to set the directory if nothing is found in existing paths."""

    global IESLibraryDirectory
    usernameDirectory = os.getenv("HOME").replace(
        "\\", "/"
    )  # Get "C:/Users/<username>"

    # Check for common installation paths
    if os.path.isdir("Z:/Maya/scripts/IES_Library"):
        IESLibraryDirectory = "Z:/Maya/scripts/IES_Library"
        return
    elif os.path.isdir(f"{usernameDirectory}/Documents/maya/scripts/IES_Library"):
        IESLibraryDirectory = f"{usernameDirectory}/Documents/maya/scripts/IES_Library"
        return

    # Handles installation case if no folder is set
    if len(IESLibraryDirectory) == 0 or not os.path.isdir(IESLibraryDirectory):
        # Popup for user to select directory with the files needed
        
        IESLibraryDirectory = cmds.fileDialog2(fileMode=3,dialogStyle=1)[0]
        if IESLibraryDirectory is None:
            sys.exit()
        while IESLibraryDirectory.split("/")[-1] != "IES_Library":
            UI_invaldLibraryPath = cmds.confirmDialog(
                title="Not valid directory",
                message="Please select the folder 'IES_Library' and click 'save'.",
                button=["Cancel","Ok"],
                cancelButton="Cancel",
                defaultButton="Ok")
            if UI_invaldLibraryPath == "Cancel":
                sys.exit()
            IESLibraryDirectory = cmds.fileDialog2(fileMode=3, dialogStyle=1)[0]

        # Write new custom file path to the file so popup isn't needed in the future
        if os.path.isdir(IESLibraryDirectory):
            with open(f"{IESLibraryDirectory}/IES_Library.py", "r") as IESpy:
                fileLines = IESpy.readlines()

                for i, line in enumerate(fileLines):
                    if fileStringMatch(line):
                        fileLines[i] = (
                            f'IESLibraryDirectory = "{IESLibraryDirectory}" # Sets folder for IES library tool\n'
                        )
                        break
                    if i > 100:
                        break
            with open(f"{IESLibraryDirectory}/IES_Library.py", "w") as IESpy:
                IESpy.writelines(fileLines)
        else:
            cmds.warning("No valid path found")
            sys.exit()


def killAllJobs(jobList) -> None:
    """Kills list of active jobs. Used when closing the window"""
    for job in jobList:
        cmds.scriptJob(kill=job)


# End functions
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# Start script

if __name__ == "__main__":
    # Ensure saved directory is still valid
    checkIESDirectory()
    # Create window
    createIESWindow()
