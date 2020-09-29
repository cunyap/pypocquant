# pyPOCQuant quick start

To analyze and compare the results among different test runs in a reproducible way with __pyPOCQuant__ please follow the following instructions for preparing the acquisition setup, the acquisition itself and the analysis of the images from lateral flow assays (LFA) / point of care tests (POCT).

This _quick start_ guide focuses on the most relevant points. For detailed information read the relevant section in the _user manual_ (Help -> Manual) .



## Preparation of the imaging acquisition setup

#### Materials needed:

* Camera for example SLR/mirror less (recommended, use raw and jpg), pocket camera, mobile phone

* POCT Template / mount

* A tripod to mount the camera above the POCT template and mount. Alternatively also a 

    box for example standard plastic box or even a shoe box can be used to mount the camera at a defined distance above the POCT template

* Tape, glue, scissors or scalpel to fix and build the mounts.

* Printer to print the POCT template and the sample QR labels

* Power bar to charge the camera batteries or power it directly

* Computer for example laptop transfer the images and run __pyPOCQuant__.

#### Instruction to build the POCT mount with the POCT template

Print our generic template (get it from the repo or the UI under Help -> POCT template) in black and white (ideally non glossy to avoid disturbing reflections) and place the POCT to evaluate in the center of the QR code box and cut out its cartridge outline with a scalpel or scissors (Fig. 1). The fine red grid will help you to align the POCT nicely with the QR code box border. _Note: needs to be repeated for each cartridge design if its size changes._

Glue or stick the template on one or two cartons and again cut out the region to place the POCT (Fig. 2). _Note: the narrower you cut the better it will hold the POCT at the exact same position._

The basis of the template mount could also be 3D printed or laser cut from any material and aligned with the POCT template to build a solid POCT mount.

| Fig. 1                                                  | Fig. 2                                      |
| ------------------------------------------------------- | ------------------------------------------- |
| ![Laufblatt_FHNW_v1-01](setup\Laufblatt_FHNW_v1-01.png) | ![POCT mount](setup\ImagingTemplate-01.png) |



#### Instructions to build the photo box / acquisition station

While setting up the imaging acquisition station there are three important points to consider. 

 * First make sure that you have __constant lightning conditions__. If just using the POCT template and a tripod (Fig. 3) make sure you have a dark room otherwise daylight changes during the day and will influence the images. Best would be using a photo box (Fig.4). _Note: Our POCT template changed over the course of the development but we don't have images of the setup from each stage. Here you see a very early incomplete version of it. Please us the one presented in Fig. 1_

 * Second make sure that during a series of tests of the same kind __the camera is well fixed on the tripod__. Ideally you use the camera timer option or a remote control to release the images to make sure that the distance between the camera and the POCT on the POCT template is constant

 * Third make sure that __the field of view does not change during a series__. For this the POCT template is well fixed on the table and tripod with camera is not moved. If you don't you will need to create a config file for each image and are not able to batch process them easily.

   | Fig. 3                                      | Fig. 4                                      |
   | ------------------------------------------- | ------------------------------------------- |
   | ![SimpleSetup-01](setup\SimpleSetup-01.png) | ![SetupFigure-01](setup\SetupFigure-01.png) |

   

## Image acquisition



Do __not write or stick anything on the POCT__. Use the QR code labels instead to allow for machine readable identification of the sample and place the QR above the QR code box in its dedicated place.



Step 1: 

* Check that __all QR codes on the template__ are in the field of view and on the image

Step 2:

* Check that the light conditions are constant and __no shadows on the POCT / sensor area__ as well as __no reflections__.

Step 3:

* Check that there are no vibrations during the acquisition which could lead to a bad / unsharp image.. If possible use __a remote control or computer control to take images__. If not available use the timer option carefully to not move the camera.

Step 4:

* Check that the image __is sharp and in focus especially the POCT sensor area as well as the QR codes__



| Example image meeting all criteria's sufficiently except that the packaging is cut off. Note: pyPOCQuant will detect the orientation of the image automatically. There is no need to rotate the images |
| ------------------------------------------------------------ |
| ![IMG_8489](demo_image\IMG_8489.JPG)             |



## Analysis of the images with pyPOCQuant



* Follow the installer guide lines to install __pyPOCQuant__
* Install tesseract by following these steps: https://tesseract-ocr.github.io/tessdoc/Home.html depending your operating system

![ui_full_empty](ui_images\ui_full_empty.JPG)

Note: For most images it is sufficient to just load an image (Step 3 & 4) and draw the sensor (Step 5) and then test the automatically determined & default parameters with (Step 7) and finally run it on all images (Step 8).



Step 1: 

* Copy the images of the same kind into a folder. Same kind is i.e same POCT cartridge / manufacturer or same imaging station (objective, distance to the sample). _Note we have a script which enables you to sort the images by manufacturer (if  included in the QR code labels) which does the splitting automatically. For the details read the respective section in the user manual (`Help $\rightarrow$ User manual`)._

Step 2:

* Run __pyPOCQuant__


Step 3:

* Select the image folder you want to analyze. Click `Ctrl+I` or on `browse` input folder.
* (Optional) select the result folder you want to analyze. By default it creates a subfolder in the input folder. Click on `browse` result folder.

Step 4:

* Click on one image (ideally one which shows all 3 bands) to load it. After a while (green progress bar fully to the right) the POCT area will be extracted and displayed on the right top.

  | Image selected - strip extraction pending | Image selected - strip extraction done & displayed |
  | ----------------------------------------- | -------------------------------------------------- |
  | ![ui_loading](ui_images\ui_loading.JPG)   | ![ui_loaded](ui_images\ui_loaded.JPG)              |


Step 5:

* Hit the draw sensor icon and click into the image and draw a rectangle around the sensor area.

  The parameters `sensor_center`, `sensor_size` and `sensor_search_area` will be set automatically in this step.

  | Click into the corners of the sensor to draw the sensor outline | Drawing finished. Parameters `sensor_center`, `sensor_size` and `sensor_search_area` have now been set automatically |
  | ------------------------------------------------------------ | ------------------------------------------------------------ |
  | ![ui_drawing](ui_images\ui_drawing.JPG)                      | ![ui_new_settings](ui_images\ui_new_settings.JPG)            |


Step 6:

* Adjust the expected position of the bands by clicking on the vertical violet lines and move them in place such that they are centered and overlapping with the bands on the test. Optionally you can also fine adjust by changing the parameters in the tree.

| Not properly aligned control band line (vertical violet line). `peak_expected_relative_location`=(0.22, 0.5, 0.7) | Properly aligned band lines `peak_expected_relative_location`=(0.22, 0.5, 0.77) |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| ![ui_moving_bar](ui_images\ui_moving_bar.JPG)                | ![ui_bar_aligned](ui_images\ui_bar_aligned.JPG)              |

Step 7 

* Change the band labels for t2, t1 and ctl band according to the test analyzed. For example `sensor_band_names=(IgG, IgM, Ctl)`. These names will be used as prefixes in the header of the result table.

Step 7:

* Hit `Test parameters` and check the result based on the quality control images. If you get false positive detections for weak signals increase the advanced parameter `sensor_thresh_factor` and hit test again.

* If the result looks good (image with the band detection i.e `IMAGE_NAME_peak_overlays control image`, and `IMAGE_NAME_peak_analysis control image`), results in the quantification data.csv you can continue. Otherwise adjust the parameters above a bit or if still not good check the advance parameters in the manual or the common problems and solutions below.

  | IMAGE_NAME_peak_overlays control image                       | IMAGE_NAME_peak_analysis control image                       |
  | ------------------------------------------------------------ | ------------------------------------------------------------ |
  | ![IMG_8489_JPG_peak_overlays](demo_image\IMG_8489_JPG_peak_overlays.png) | ![IMG_8489_JPG_peak_analysis](demo_image\IMG_8489_JPG_peak_analysis.png) |

  

Step 8:

  Hit `Run` to batch analyze all images in the folder in parallel.

  

  Repeat the procedure for all other folders. _Note: if the POCT cartridge design changes or a different camera with a different perspective is used a new config has to be generated and tested. Otherwise one can load the same config file also for other / new images. To load a config file just double click it or `Ctrl+O` or `File $\rightarrow$ Load settings from file`_





## Potential problems and their solution:



__Problem__: There are artifacts / weak signals that get quantified wrongly as a band (Fig. 5)

__Solution__: Increase the `sensor threshold factor` (Fig. 6)

| Fig 5 `sensor threshold factor=1`                            | Fig 6 `sensor threshold factor=2`                            |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| ![Img1966_jpg_peak_analysis_th1](problem_solutions\Img1966_jpg_peak_analysis_th1.png) | ![Img1966_jpg_peak_analysis](problem_solutions\Img1966_jpg_peak_analysis.png) |
| ![Img1966_jpg_peak_overlays_th1](problem_solutions\Img1966_jpg_peak_overlays_th1.png) | ![Img1966_jpg_peak_overlays_th2](problem_solutions\Img1966_jpg_peak_overlays_th2.png) |

__Problem__: _No_ or _not all_ or _the wrong band(s)_ were not detected (Fig. 7)

__Solution__: Adjust the `Peak expected relative location` parameter for the band(s) which were not detected. If that did not solve the problem check the qc images if the sensor was detected correctly. If not adjust the sensor position and its size (Fig. 8).

| Fig 7                                                        | Fig 8                                                        |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| ![Img1966_jpg_peak_analysis_wb](problem_solutions\Img1966_jpg_peak_analysis_wb.png) | ![Img1966_jpg_peak_analysis](problem_solutions\Img1966_jpg_peak_analysis.png) |
| ![Img1966_jpg_peak_overlays_wb](problem_solutions\Img1966_jpg_peak_overlays_wb.png) | ![Img1966_jpg_peak_overlays_th2](problem_solutions\Img1966_jpg_peak_overlays_th2.png) |

__Problem__: Almost no pixels are considered for quantification (Fig. 9)

__Solution__: Reduce the `sensor border x|y` values to consider more pixels of the sensor (Fig. 10). If it considers too many pixels increase the parameter values.

| Fig 9 `sensor border x|y=25`                                 | Fig 10  `sensor border x|y=7`                                |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| ![Img1966_jpg_peak_overlays_narrow](problem_solutions\Img1966_jpg_peak_overlays_narrow.png) | ![Img1966_jpg_peak_overlays](problem_solutions\Img1966_jpg_peak_overlays.png) |

__Problem__: I have a lot of images to be processed and it is slow.

__Solution__: Increase the `Number of cores` parameter to the maximum of your computer. Use a more powerful station or cluster.

__Problem__: By accident the image was taken with the POCT wrongly oriented and the control band is left (Fig. 11).

__Solution__: Select the checkbox `try to correct strip orientation`. This will try to rotate the image correctly for the analysis (Fig 12). The qc image lets you verify if the correction works. If it does not work modify the parameters  (_Relative height factor_, Relative center cut-off_, _Relative border cut-of_) defining the size and position of the rectangles. The red rectangle indicates (Fig. 11) where the inlet was found and will rotate the image such that the inlet is left and the control band on the right (Fig 12). They should only include the region around the pipetting inlet. If it still does not work your last chance is if there is some text on the POCT which we might be able to read. Add the prominent text such as i.e. COVID to the `Strip text to search (orientation)` parameter and select if the text is on the right or not `Strip text is on the right`. Checked equals to the text is on the right. If this still fails you have to repeat that image.

| Fig 11                                                       | Fig 12                                                       |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| ![IMG_9524_JPG_strip_gray_hough_analysis_candidates](problem_solutions\IMG_9524_JPG_strip_gray_hough_analysis_candidates.png) | ![IMG_9524_JPG_strip_gray_hough_analysis](problem_solutions\IMG_9524_JPG_strip_gray_hough_analysis.png) |

__Problem__: I have a lot of images from with different POCT cartridge designs from different manufacturers taken with the same camera but my config file does only work for one type.

__Solution__: Split the images into a subfolder for each cartridge design / manufacturer. If you used the QR code sample labels you can use the script described in the manual to do this automatically for you. 

__Problem__:  I have a lot of images with different POCT cartridge designs from different manufacturers  do I really need a separate config for each design?

__Solution__: Unfortunately yes. As they come in any shape the software needs some specific guidance to know where to search for the bands to allow for robust and reproducible results. One solution to relax this assumption would be to change the POCT cartridge design by including small qr codes directly  next to the sensor. That would allow us also to get rid of the QR code template. If you have contact to the manufacturers tell them about it and their potential competitive advantage in the market (Fig 13)! 

| Fig 13                                        |
| --------------------------------------------- |
| ![NewPCTDesign-01](setup\NewPCTDesign-01.png) |









