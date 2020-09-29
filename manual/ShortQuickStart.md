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




## Image analysis



Step 1: 

* Copy the images of the same kind into a folder. Same kind is i.e same POCT cartridge / manufacturer or same imaging station (objective, distance to the sample). _Note we have a script which enables you to sort the images by manufacturer (if  included in the QR code labels) which does the splitting automatically. For the details read the respective section in the user manual (`Help $\rightarrow$ User manual`)._

Step 2:

* Run __pyPOCQuant__

  ![ui_full_empty](ui_images\ui_full_empty.JPG)

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
  | ![IMG_8489_JPG_peak_overlays](ui_images\sample_image\test\IMG_8489_JPG_peak_overlays.png) | ![IMG_8489_JPG_peak_analysis](ui_images\sample_image\test\IMG_8489_JPG_peak_analysis.png) |

  

Step 8:

  Hit `Run` to batch analyze all images in the folder in parallel.

  

  Repeat the procedure for all other folders. _Note: if the POCT cartridge design changes or a different camera with a different perspective is used a new config has to be generated and tested. Otherwise one can load the same config file also for other / new images. To load a config file just double click it or `Ctrl+O` or `File $\rightarrow$ Load settings from file`_

  

  