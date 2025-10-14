"""WARNING, this file should not be edited"""

import maya.standalone
import maya.cmds as cmds
import sys
import os

maya.standalone.initialize(name='python')

iesFiles = sys.argv[1].split(",")
IESLibraryDirectory = sys.argv[2]
renderEngine = sys.argv[3]
processImages = sys.argv[4]
newScenePath = sys.argv[5]
IESImageDirectory = IESLibraryDirectory + "/IES_images/"
#iesFiles = cmds.getFileList(filespec="*.ies",folder=IESLibraryDirectory+"/IES_files")
camera = "renderCam"

# Open the thumbnail scene copy
cmds.file(IESLibraryDirectory+newScenePath, open=True, force=True)

def logMessage(message):
    """Logs message to command prompt window"""
    print(message)
    sys.stdout.flush()

def prerender_Arnoldsettings(profile_name, output_dir, camera_name, start_frame, end_frame, step_frame = 1, image_format = 'png'):
    # Create output dir if not exists.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Create output file name with camera name and resolution parametrs.
    output_file_base_name = 'light_'

    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')

    # Set "defaultArnoldRenderOptions" "renderGlobals" attribut from "defaultRenderGlobals" node attributes.
    cmds.setAttr('defaultArnoldRenderOptions.renderGlobals', 'defaultRenderGlobals', type = 'string')

    # Set "defaultArnoldDriver" attribut for output render file format ("exr").
    cmds.setAttr('defaultArnoldDriver.aiTranslator', image_format, type = 'string')
    #cmds.setAttr('defaultArnoldDriver.outputMode', 2)

    # Set defaultRenderGlobals attributes for prefix (replace default render path)
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', output_file_base_name, type = 'string')
    cmds.setAttr('defaultRenderGlobals.useFrameExt', 1)
    cmds.setAttr("defaultRenderGlobals.animation", True)

    # Set defaultRenderGlobals attributes for animation range
    cmds.setAttr('defaultRenderGlobals.startFrame', start_frame)
    cmds.setAttr('defaultRenderGlobals.endFrame', end_frame)
    cmds.setAttr('defaultRenderGlobals.byFrameStep', step_frame)

def prerender_Redshiftsettings(profile_name, output_dir, camera_name, start_frame, end_frame, step_frame = 1, image_format = 2):
    # Create output dir if not exists.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Create output file name with camera name and resolution parametrs.
    output_file_base_name = 'light_'

    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'redshift', type='string')

    cmds.setAttr('redshiftOptions.imageFormat', image_format)

    # Set defaultRenderGlobals attributes for prefix (replace default render path)
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', output_file_base_name, type = 'string')
    cmds.setAttr('defaultRenderGlobals.useFrameExt', 1)
    cmds.setAttr("defaultRenderGlobals.animation", True)

    # Set defaultRenderGlobals attributes for animation range
    cmds.setAttr('defaultRenderGlobals.startFrame', start_frame)
    cmds.setAttr('defaultRenderGlobals.endFrame', end_frame)
    cmds.setAttr('defaultRenderGlobals.byFrameStep', step_frame)

def createLights(defaultLightName, iesAttr, iesFilesList):
    """Creates lights from a list of IES files using a default
    light and iesAttribute compatible with setAttr.
    Uses Arnold photometric lights or Redshift IES lights"""
    
    # Set Default Light to existing profile to ensure no errors in render
    cmds.setAttr("aiPhotometricLightShape.aiFilename", IESLibraryDirectory+"/IES_files/"+iesFilesList[0]+".ies", type="string")
    cmds.setAttr("rsIESLightShape.profile", IESLibraryDirectory+"/IES_files/"+iesFilesList[0]+".ies", type="string")

    for iteration, iesFile in enumerate(iesFilesList):
        frame = iteration + 1
        profileName = iesFile #.split(".")[0]
        newLight = cmds.duplicate(defaultLightName, name=profileName)
        cmds.setAttr(f"{profileName}Shape.{iesAttr}", IESLibraryDirectory+"/IES_files/"+iesFile+".ies", type="string")

        # Set visibility for only 1 frame
        cmds.setKeyframe(newLight, attribute='visibility', t=frame-1, v=False)
        cmds.setKeyframe(newLight, attribute='visibility', t=frame, v=True)
        cmds.setKeyframe(newLight, attribute='visibility', t=frame+1, v=False)

match renderEngine:
    case "arnold" | "Arnold":
        renderEngine = "arnold"
        cmds.setAttr("ArnoldLayer.visibility", True)
        cmds.setAttr("RedshiftLayer.visibility", False)

        # Prep render settings for arnold rendering
        prerender_Arnoldsettings("iesLight_", IESImageDirectory, camera, 1, len(iesFiles))

        # Create lights for missing thumbnail profiles
        createLights("aiPhotometricLight", "aiFilename", iesFiles)
    case "redshift" | "Redshift":
        renderEngine = "redshift"
        cmds.setAttr("ArnoldLayer.visibility", False)
        cmds.setAttr("RedshiftLayer.visibility", True)

        # Prep render settings for redshift rendering
        prerender_Redshiftsettings("iesLight_", IESImageDirectory, camera, 1, len(iesFiles))

        # Create lights for missing thumbnail profiles
        createLights("rsIESLight", "profile", iesFiles)
    case "both" | "Both":
        cmds.setAttr("ArnoldLayer.visibility", True)
        cmds.setAttr("RedshiftLayer.visibility", True)
        
        createLights("aiPhotometricLight", "aiFilename", iesFiles)
        createLights("rsIESLight", "profile", iesFiles)
    case _:
        pass

cmds.file(save=True)

maya.standalone.uninitialize()