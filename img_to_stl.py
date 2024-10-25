import numpy as np
from stl import mesh
import cv2
import os
from typing import Tuple, Optional
import argparse


class ImageToSTL:
    def __init__(self, scale_factor: float = 1.0, base_height: float = 2.0):
        self.scale_factor = scale_factor
        self.base_height = base_height

    def process_image(
        self,
        img_path: str,
        output_path: str,
        blur: Optional[Tuple[int, int]] = None,
        invert: bool = False,
        max_height: float = 10.0,
        threshold: Optional[int] = None,
    ) -> None:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Input image not found: {img_path}")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        try:
            # Read image with alpha channel
            print(f"Reading image: {img_path}")
            img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError(f"Failed to load image: {img_path}")

            # Handle transparency
            if img.shape[-1] == 4:  # If image has alpha channel
                print("Processing transparent PNG...")
                # Split the image into color and alpha channels
                alpha = img[:, :, 3]

                # Create a white background
                white_background = np.ones_like(img[:, :, :3]) * 255

                # Calculate foreground ratio based on alpha
                alpha_3d = np.stack([alpha, alpha, alpha], axis=-1) / 255.0

                # Combine foreground and background
                img = (
                    img[:, :, :3] * alpha_3d + white_background * (1 - alpha_3d)
                ).astype(np.uint8)

            # Convert to grayscale
            print("Converting to grayscale...")
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply threshold if specified
            if threshold is not None:
                print(f"Applying threshold at level {threshold}...")
                _, gray_img = cv2.threshold(gray_img, threshold, 255, cv2.THRESH_BINARY)

            # Apply blur if specified (after threshold)
            if blur:
                print(f"Applying Gaussian blur with kernel size {blur}...")
                gray_img = cv2.GaussianBlur(gray_img, blur, 0)

            # Scale the height values
            height_scale = max_height / 255.0

            # Generate 3D mesh
            print("Generating 3D mesh...")
            vertices_array = []
            for x, row in enumerate(gray_img):
                for y, pixel in enumerate(row):
                    # Skip pixels that would have zero height after inversion
                    if invert and pixel == 255:
                        continue
                    if not invert and pixel == 0:
                        continue

                    # Scale the coordinates
                    x_scaled = x * self.scale_factor
                    y_scaled = y * self.scale_factor

                    # Calculate height based on pixel value
                    height = (255 - pixel if invert else pixel) * height_scale

                    # Create vertices for current pixel
                    vertices = np.array(
                        [
                            # Base vertices
                            [x_scaled, y_scaled, 0],
                            [x_scaled + self.scale_factor, y_scaled, 0],
                            [
                                x_scaled + self.scale_factor,
                                y_scaled + self.scale_factor,
                                0,
                            ],
                            [x_scaled, y_scaled + self.scale_factor, 0],
                            # Top vertices
                            [x_scaled, y_scaled, height + self.base_height],
                            [
                                x_scaled + self.scale_factor,
                                y_scaled,
                                height + self.base_height,
                            ],
                            [
                                x_scaled + self.scale_factor,
                                y_scaled + self.scale_factor,
                                height + self.base_height,
                            ],
                            [
                                x_scaled,
                                y_scaled + self.scale_factor,
                                height + self.base_height,
                            ],
                        ]
                    )
                    vertices_array.append(vertices)

            if not vertices_array:
                raise ValueError(
                    "No pixels to extrude! Check your threshold and invert settings."
                )

            # Define faces for a cube
            faces = np.array(
                [
                    [0, 3, 1],
                    [1, 3, 2],  # bottom
                    [0, 4, 7],
                    [0, 7, 3],  # left
                    [4, 5, 6],
                    [4, 6, 7],  # top
                    [5, 1, 2],
                    [5, 2, 6],  # right
                    [2, 3, 6],
                    [3, 7, 6],  # front
                    [0, 1, 5],
                    [0, 5, 4],  # back
                ]
            )

            # Create meshes
            print("Creating final mesh...")
            meshes = []
            for vertices in vertices_array:
                cube = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
                for i, f in enumerate(faces):
                    for j in range(3):
                        cube.vectors[i][j] = vertices[f[j], :]
                meshes.append(cube)

            # Combine all meshes
            total_length_data = sum(len(m.data) for m in meshes)
            data = np.zeros(total_length_data, dtype=mesh.Mesh.dtype)
            data["vectors"] = np.array(meshes).reshape((-1, 9)).reshape((-1, 3, 3))

            # Create and save final mesh
            print(f"Saving STL file to: {output_path}")
            mesh_final = mesh.Mesh(data.copy())
            mesh_final.save(output_path)

            print(f"\nSuccess! STL file created: {output_path}")
            print(f"Model dimensions: {gray_img.shape[1] * self.scale_factor:.1f}x{
                  gray_img.shape[0] * self.scale_factor:.1f}x{max_height + self.base_height:.1f}mm")

        except Exception as e:
            raise RuntimeError(f"Failed to process image: {str(e)}")


def parse_blur(blur_str: str) -> Tuple[int, int]:
    try:
        w, h = map(int, blur_str.split(","))
        if w % 2 == 0 or h % 2 == 0:
            raise ValueError("Blur kernel dimensions must be odd numbers")
        return (w, h)
    except:
        raise argparse.ArgumentTypeError(
            "Blur must be two odd integers separated by comma (e.g., '5,5')"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Convert an image to an STL file for 3D printing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion with default settings:
  python image_to_stl.py input.png output.stl

  # Sharp edges with no base layer:
  python image_to_stl.py input.png output.stl --threshold 128 --base-height 0 --invert

  # Set scale factor and maximum height:
  python image_to_stl.py input.png output.stl --scale 0.5 --max-height 20

  # Full example with all options:
  python image_to_stl.py input.png output.stl --scale 0.5 --base-height 0 --max-height 15 --threshold 128 --invert
        """,
    )

    parser.add_argument("input", help="Input image file path")
    parser.add_argument("output", help="Output STL file path")
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale factor for X and Y dimensions (default: 1.0)",
    )
    parser.add_argument(
        "--base-height",
        type=float,
        default=2.0,
        help="Height of the base in mm (default: 2.0)",
    )
    parser.add_argument(
        "--max-height",
        type=float,
        default=10.0,
        help="Maximum height in mm (default: 10.0)",
    )
    parser.add_argument(
        "--blur",
        type=parse_blur,
        metavar="W,H",
        help="Apply Gaussian blur with kernel size WxH (e.g., 5,5)",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert the height mapping (dark pixels become high)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        choices=range(0, 256),
        metavar="[0-255]",
        help="Threshold value for creating sharp edges (0-255)",
    )

    args = parser.parse_args()

    try:
        converter = ImageToSTL(scale_factor=args.scale, base_height=args.base_height)
        converter.process_image(
            img_path=args.input,
            output_path=args.output,
            blur=args.blur,
            invert=args.invert,
            max_height=args.max_height,
            threshold=args.threshold,
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
