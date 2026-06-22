import os
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Directory containing the images
gif_name = "inc-single-edge_19x19"
image_directory = "results/%s"%gif_name
output_gif = "gifs/%s.gif"%gif_name
frame_duration = 100.0  # Duration per frame in milliseconds
font_path = "/System/Library/Fonts/Supplemental/Helvetica.ttc"

# Get a sorted list of all image filenames in the directory
image_filenames = sorted(
    [os.path.join(image_directory, f) for f in os.listdir(image_directory) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))],
    key=lambda f: os.path.getctime(f)
)

# Process images to add a gap with text
processed_images = []
for filename in image_filenames:
    # Open the image
    image = Image.open(filename)
    image_width, image_height = image.size

    # Create a new image with extra space for text
    gap_height = 50  # Height of the gap for text
    new_height = image_height + gap_height
    new_image = Image.new("RGB", (image_width, new_height), color=(255, 255, 255))  # White background

    # Paste the original image onto the new image
    new_image.paste(image, (0, gap_height))

    # Add text (filename without directory and extension)
    draw = ImageDraw.Draw(new_image)
    font = ImageFont.truetype(font_path, 50)  # Adjust font size as needed
    text = os.path.basename(filename)

    # Calculate text width and height using textbbox
    text_bbox = draw.textbbox((0, 0), text, font=font)  # Bounding box of the text
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Center the text in the gap
    text_x = (image_width - text_width) // 2
    text_y = (gap_height - text_height) // 2
    draw.text((text_x, text_y), text, fill="black", font=font)

    # Save processed image in memory
    processed_images.append(new_image)

# Create a GIF from the processed images
with imageio.get_writer(output_gif, mode='I', duration=frame_duration, loop=0) as writer:
    for image in processed_images:
        writer.append_data(np.array(image))

print(f"GIF with text created and saved as {output_gif}")
