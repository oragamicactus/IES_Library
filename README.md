# IES Profile Library tool

## About

The *IES Profile Library* tool allows you to visually browse and apply IES (International Engineering Society) light profiles to Arnold photometric and Redshift IES lights within your Autodesk Maya scene.

### What's IES?

IES (International Engineering Society) light profiles have the file extension `.ies` which describe the light throw pattern and falloff characteristics of a light. IES files enable realistic throw patterns from real-world lights to be applies in 3D.

Typical 3D lights apply even lighting across their entire throw region with adjustable falloff characteristics (e.g. inverse square). This is not normal for most lights since the illuminating element, and reflectors cause visible distortions, and uneven lighting across their throw area. IES profiles profile an easy, realistic way to match real lights in 3D.

As an example, picture a flashlight in real life. You'll see that some spots are brighter than others, almost like there's a shadow in certain areas. This is what using IES light profiles will allow you to do in your 3D scene.

## Dependencies

**Modules**:

- `send2trash` -> included with the tool, no additional steps are required to install this. *optionally you may add to your device through the command line with the prompt `pip install send2trash` once python3 is installed*
- Standard libraries: `os`, `subprocess`, `maya.cmds`, `maya.standalone`, `sys`, `platform` (all these are standard libraries included in python 3, no additional setup required)
- **Render engines**: `Arnold*`, `Redshift*`

> At least one of the two renderers is required. Some features like **Generate thumbnails** may require different licenses, but only 1 is required for core functionality.
> 

> Operating system: This tool has only been tested in Windows 11, should work on other versions of Windows. Operating systems like MacOS and Linux may not behave as expected across all features (generate thumbnails may not work)
> 

## Installation and setup

1. Unzip the **IES_Library** folder
2. Move the unzipped folder to your desired location. Suggested locations are: `C:/Users/YOUR_USERNAME/Documents/maya/scripts/` or `Z:/Maya/scripts/`

> Note: if using a custom location you'll get a popup on first launch to specify where the IES_Library folder is. After you select the script, drag it back in to Maya and your custom location will be saved so no popup is needed in subsequent launches.
> 

## How to use

### Overview

![IES profile library user interface with annotations for profile browser, preview, compatible light list, and creation buttons](https://github.com/user-attachments/assets/344c91c7-27e9-4d5e-8600-74137d6a6373)


User interface overview

### Launching the tool

1. Drag the `IES_Library.py` file into the code editor section of Maya
2. Click **ctrl** + **Enter** while you're focused on the code editor which will open the window
3. The window will open.
    - If this is your first time opening the tool, or the library location cannot be found (see installation instructions) you'll be prompted to locate the folder where the tool, and all the images are found.
    
    > Note: Make sure to select the folder called "IES_Library" and not the image directories, or other folders within it.
    > 
4. *Optional:* Save the script to your shelf for easier access in the future.

### Applying a profile

**Method 1**

In the profile browser click on a profile image to select the profile. The preview on the right will showcase the currently selected profile.

In the list of *Compatible IES lights* click on the light shape you'd like to apply the profile to. You may use shift or control to select multiple lights to apply the same profile to.

> Note: Your scene selection will not change with this selection method
> 

**Method 2**

In the profile browser click on a profile image to select the profile. The preview on the right will showcase the currently selected profile.

In your scene, select the IES light(s) you'd like to apply a profile to. You may select groups and use shift or control to select multiple. You'll see the tool matches your selection.

> Note: Only IES compatible lights will be selected with this tool. All other light types that are not Arnold Photometric lights or Redshift IES lights will be ignored. You may also select other things like geometry, the tool can only interact with IES lights.
> 

### Creating a light

IF you want to create a new IES compatible light, click **Create light** in the bottom of the tool. This will create a new light at the origin of your scene. The light will match the render engine you're using so ensure you have Arnold or Redshift selected in your render settings so the type matches your desired result.

### Adding custom profile images

This tool takes images from the `/IES_images` folder and matches them to IES files in the `/IES_files` folder. The name of the file must be identical, except the extensions. Images should be `.png` format, ies files should be `.ies`.

To add your own images, or replace the existing images you will need to add custom images to the `/IES_images` folder in the tool directory, make sure the naming matches the file exactly. If the tool is already open within Maya, close and reopen it to view changes to the images.

> Note, this tool has a feature to automatically generate images for IES files that don't yet have an image. See Generate thumbnails section for how to do this.
> 

### Generate thumbnails

The **Generate thumbnails** button will create thumbnails for any ies files that have been added and don't have a matching `.png` image in the *IES_images* folder.

1. Click image icon in bottom left corner
2. Select option for thumbnail generation (see *Generate thumbnails options* below)
3. Maya will show a confirmation message that the process has begun.

<aside>
<img src="https://www.notion.so/icons/help-alternate_gray.svg" alt="https://www.notion.so/icons/help-alternate_gray.svg" width="40px" /> If you need to stop this process, open task manager with **Ctrl** + **Shift** + **Esc** and stop **mayapy3** or **mayaBatch** (mayapy3 runs when building the scene, mayaBatch runs when rendering).

</aside>

1. You’ll see a notification that the thumbnail generating process is complete (check windows notifications). You may continue to use Maya while this runs but note that rendering is taking place in the background, it’s suggested that you don’t do heavy processes while this runs (such as render your current scene).  **Do not** turn off your computer, or enter sleep while this is running.

> NOTE: if you have added images to the `IES_images` folder and don't see them, make sure they're in **png** format and the name of the file matches the ies file it is for. For example spotlight_01.ies should have an image named spotlight_01.png
> 

**Generate thumbnails options**

There are a few options when generating thumbnails. You may automatically generate thumbnails using the Arnold or Redshift render engines. These do not impact which engines can use the ies files, they are just used to make the thumbnail images.

When generating thumbnails a new scene will appear temporarily in the IES_Library directory. This is used only while rendering and will be deleted once rendering is complete (unless using **manual** option). If you need to modify the scene for any reason you can reveal hidden folders in windows explorer to open and make adjustments to *IESMakeThumbnails.ma*. **DO NOT make changes to the naming of lights or render layers in the *IESMakeThumbnails.ma* scene, this will break the automated thumbnail generator**.

**Arnold**

- CPU based render.
- Batch license required (watermark will be present without this).

**Redshift**

- GPU based render.
- Can be faster on machines with good graphics cards.
- License required or this will fail.

**Manual**

- Scene is built with lights automatically.
- Rendering the images is up to you, feel free to mess around with the scene.

> NOTE: It is recommended that you rename or delete the new scene once you finish using it. It may cause issues with subsequent thumbnail generate processes if left with the original name.
> 

**Cancel**

- Aborts the thumbnail generator, no action is taken.

### Help button (?)

Opens this document for easy reference

### Folder button

Opens the folder the tool is installed to. Useful if you need to open the manually created thumbnail scene, or to add additional IES profiles to the tool.

### Hidden files and folders

There are several hidden files and folders as part of this package. These are meant to be hidden and should not be edited. If you need to make changes to these for any reason you may open the windows file explorer and select **View** > **Show** > **Hidden items.**

<aside>
<img src="https://www.notion.so/icons/private_gray.svg" alt="https://www.notion.so/icons/private_gray.svg" width="40px" /> WARNING: Do not delete these files, modifying them is likely to break the tool’s functionality. You’re in the danger zone here, tread carefully.

</aside>

The hidden items are:

- batchProcess.bat
- IESMakeThumbnails.ma
- IESmayaSceneSetup.py
- cleanupFiles.py
- windowsNotification.py
- send2trash (folder)

If you see any of these items in the folder, don’t mess with them and feel free to mark as hidden by right clicking and selecting **Properties**, then in the properties panel select **Hidden** and click **Apply.**
