**ImageToSTL**

This Python script converts a grayscale image into a 3D printable STL file. It extrudes the image pixels into a mesh, where darker pixels correspond to higher elevations.

**Features:**

* Supports PNG and other image formats with alpha channel (transparency)
* Handles transparent backgrounds for cleaner output
* Offers options for:
    * Scaling the model dimensions
    * Setting a base height for the model
    * Applying Gaussian blur for smoother transitions
    * Inverting the height mapping (dark for high, light for low)
    * Setting a threshold for creating sharp edges

**Installation**

1. Make sure you have Python 3 and the required libraries (`numpy`, `stl`, `opencv-python`) installed. You can install them using `pip`:

   ```bash
   pip install numpy stl opencv-python
   ```

2. Clone this repository or download the script.

**Usage**

Run the script from the command line using the following syntax:

```bash
python image_to_stl.py input_image.png output.stl [options]
```

**Arguments:**

* `input_image.png`: Path to the input grayscale image file (or any supported format with alpha channel).
* `output.stl`: Path to the output STL file.
* `--scale`: Scale factor for X and Y dimensions (default: 1.0).
* `--base-height`: Height of the base in millimeters (default: 2.0).
* `--max-height`: Maximum height in millimeters (default: 10.0).
* `--blur`: Apply Gaussian blur with kernel size WxH (e.g., `--blur 5,5`).
* `--invert`: Invert the height mapping (dark pixels become high).
* `--threshold`: Threshold value for creating sharp edges (0-255).

**Examples:**

* Basic conversion with default settings:

   ```bash
   python image_to_stl.py input.png output.stl
   ```

* Sharp edges with no base layer:

   ```bash
   python image_to_stl.py input.png output.stl --threshold 128 --base-height 0 --invert
   ```

* Set scale factor and maximum height:

   ```bash
   python image_to_stl.py input.png output.stl --scale 0.5 --max-height 20
   ```

**Additional Notes**

* For best results, ensure your input image has good contrast and lighting.
* The script provides detailed information about the created STL file, including its dimensions.
* Feel free to modify the script to suit your specific needs.

I hope this README helps!
