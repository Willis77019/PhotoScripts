#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Core segment to Video Generator


# In[ ]:


"""
=============================================================================
Core Segment to Video Generator
=============================================================================
Description:
    Generates a continuous scrolling video (up to 4K portrait) from a 
    folder of stitched core columns. The video simulates a "fly-through" 
    camera panning seamlessly from the bottom of the core sequence to the top.

    File setup: The program expects that files will load as sorted, with the 
    first (top most) core stripe at the top of the list and successivly older 
    cored rock lower in the list.

    Smart Depth Mode & Gap Detection:
    If images are named with top and bottom depths (e.g., "name_1200.5_1210.0.jpg"), 
    the script automatically generates an interpolated depth scale alongside 
    the core and inserts "MISSING INTERVAL" warning blocks for depth gaps.
    Standard alphabetical naming defaults to a continuous, unscaled render.

    Architecture Note:
    Utilizes a custom "Direct Streaming" architecture to bypass standard JPEG 
    height limits (65,535 pixels) and prevent massive RAM overflows. It maps 
    images virtually and only crops/resizes the exact pixels needed for the 
    current frame directly from the hard drive.

Prerequisites:
    pip install opencv-python numpy

Usage Instructions:
    1. Configuration: Adjust FPS, FONT_SCALE, decimal precision, and tick 
       thickness in the "Advanced Render Settings" block below as needed.
    2. Run the script. A folder selection dialog will appear.
    3. Select the "Stitched_Output" folder containing your core images.
    4. Enter Video Resolution (720, 1080, or 4K):
       * Best Practice: 720p for standard unscaled viewing, 1080p for depth 
         labels, and 4K only for special high-resolution imaging.
    5. Enter Zoom Factor (1 = full width, 2 = half-width/longer vertical run):
       * Best Practice: Zoom 1.0 overlays depth labels directly onto the rock 
         with a readability outline. Zoom 1.25+ places labels cleanly beside 
         the core in a dedicated black margin.
    6. Enter the desired total duration of the video in seconds.

Output:
    Generates a 60 FPS MP4 video dynamically named with resolution and zoom
    (e.g., "core_flythrough_1080p_Zoom2.0.mp4") in the selected directory.
=============================================================================
"""

import cv2
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog
import re
import math

# ==========================================
# --- ADVANCED RENDER SETTINGS ---
# Adjust these variables to customize the video output
# ==========================================
FPS = 60                   # Frames per second for smooth scrolling
FONT_SCALE = 1.5           # Size of the depth label text
FONT_THICKNESS = 2         # Thickness of the depth label text
MAJOR_TICK_THICKNESS = 3   # Thickness of major foot/decimeter ticks
MINOR_TICK_THICKNESS = 2   # Thickness of minor tenth/centimeter ticks

# Precision Settings for Depth Labels
DECIMAL_PLACES_METRIC = 1  # Number of decimal places when units are meters
DECIMAL_PLACES_FEET = 0    # Number of decimal places when units are feet (0 = integers only)
# ==========================================

def create_core_video_direct_stream():
    # 1. Setup Environment
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True) 
    root.attributes('-topmost', False)

    folder = filedialog.askdirectory(title="Select 'Stitched_Output' Folder")
    if not folder: return

    # Resolution Selection
    res_str = simpledialog.askstring("Resolution", "Enter desired quality (4K, 1080, or 720):", initialvalue="1080")
    if not res_str: return
    res_str = res_str.upper()

    if "4K" in res_str:
        WIDTH, HEIGHT = 2160, 3840
        base_name = "core_flythrough_4K"
    elif "720" in res_str:
        WIDTH, HEIGHT = 720, 1280
        base_name = "core_flythrough_720p"
    else:
        WIDTH, HEIGHT = 1080, 1920 # Default fallback
        base_name = "core_flythrough_1080p"

    # Zoom Factor Selection
    zoom_factor = simpledialog.askfloat(
        "Zoom Factor", 
        "Enter zoom factor\n(1 = full width, 2 = half width/twice the length, etc.):", 
        initialvalue=1.0, minvalue=1.0, maxvalue=20.0
    )
    if not zoom_factor: return

    duration_sec = simpledialog.askinteger("Input", "Total video duration (seconds):", minvalue=1)
    if not duration_sec: return

    # Initial calculation of rock width and centering offset
    ROCK_WIDTH = int(WIDTH / zoom_factor)
    X_OFFSET = (WIDTH - ROCK_WIDTH) // 2

    output_name = f"{base_name}_Zoom{zoom_factor}.mp4"
    output_path = os.path.join(folder, output_name)

    # 2. Get Images and Detect "Depth Mode"
    valid_extensions = ('.jpg', '.jpeg', '.png')
    raw_files = [f for f in os.listdir(folder) if f.lower().endswith(valid_extensions)]
    
    if not raw_files:
        print("No images found.")
        return

    # Regex looks for "Number_Number.extension" at the end of the filename
    depth_pattern = re.compile(r'(\d+(?:\.\d+)?)[_ -](\d+(?:\.\d+)?)\.(?:jpg|jpeg|png)$', re.IGNORECASE)
    
    parsed_images = []
    depth_mode = True

    for filename in raw_files:
        match = depth_pattern.search(filename)
        if match:
            d1, d2 = float(match.group(1)), float(match.group(2))
            top_d = min(d1, d2)
            bot_d = max(d1, d2)
            parsed_images.append({
                'path': os.path.join(folder, filename),
                'top': top_d,
                'bot': bot_d
            })
        else:
            depth_mode = False
            parsed_images.append({'path': os.path.join(folder, filename)})

    unit = ""
    if depth_mode:
        # Sort by physical top depth (shallowest to deepest)
        parsed_images.sort(key=lambda x: x['top'])
        unit = simpledialog.askstring("Depth Detected", "Depth labels detected!\nEnter unit (e.g., m, ft) or leave blank:", initialvalue="m")
        if unit is None: unit = ""
    else:
        # Standard alphabetical sorting
        parsed_images.sort(key=lambda x: x['path'])

    total_frames = duration_sec * FPS

    # 3. Step 1: Map the virtual column 
    print(f"Step 1/2: Mapping core images for {HEIGHT}p output (Zoom: {zoom_factor}x)...")
    if depth_mode: print("--> Depth Mode Active: Calculating gaps and generating labels.")
    
    chunk_metadata = []
    total_virtual_height = 0
    
    # We use part of the left pillar-box to draw the text. max() prevents crashes at 1.0 zoom.
    margin_w = max(0, min(400, X_OFFSET - 20)) if depth_mode else 0

    for idx, item in enumerate(parsed_images):
        # --- Handle Gaps (Depth Mode Only) ---
        if depth_mode and idx > 0:
            prev_bot = parsed_images[idx-1]['bot']
            current_top = item['top']
            
            # If there is a gap > 0.01 units
            if current_top > prev_bot + 0.01:
                gap_h = int(HEIGHT * 0.4) # Make the gap take up 40% of the screen height
                chunk_metadata.append({
                    'id': f"gap_{idx}",
                    'type': 'gap',
                    'v_start': total_virtual_height,
                    'v_end': total_virtual_height + gap_h,
                    'virtual_h': gap_h,
                    'top': prev_bot,
                    'bot': current_top
                })
                total_virtual_height += gap_h

        # --- Handle Core Image ---
        img = cv2.imread(item['path'])
        if img is None: continue
        
        orig_h, orig_w = img.shape[:2]
        scale = ROCK_WIDTH / orig_w
        virtual_h = int(orig_h * scale)
        
        chunk_metadata.append({
            'id': item['path'],
            'type': 'core',
            'path': item['path'],
            'v_start': total_virtual_height,
            'v_end': total_virtual_height + virtual_h,
            'virtual_h': virtual_h,
            'top': item.get('top'),
            'bot': item.get('bot')
        })
        total_virtual_height += virtual_h
        print(f"  Mapped {idx+1}/{len(parsed_images)}")

    if total_virtual_height < HEIGHT:
        print("Error: Total core height is shorter than the video window. Try a smaller zoom factor.")
        return

    # 4. Step 2: Direct Streaming Render
    print(f"\nStep 2/2: Rendering {total_frames} frames...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, FPS, (WIDTH, HEIGHT))

    start_y = total_virtual_height - HEIGHT
    end_y = 0
    image_cache = {}

    for i in range(total_frames):
        progress = i / (total_frames - 1) if total_frames > 1 else 0
        current_y = int(start_y + (end_y - start_y) * progress)
        camera_end_y = current_y + HEIGHT
        
        frame_pieces = []
        
        for chunk in chunk_metadata:
            if not (chunk['v_end'] <= current_y or chunk['v_start'] >= camera_end_y):
                overlap_v_start = max(current_y, chunk['v_start'])
                overlap_v_end = min(camera_end_y, chunk['v_end'])
                
                local_v_start = overlap_v_start - chunk['v_start']
                local_v_end = overlap_v_end - chunk['v_start']
                
                # Render and Cache the Chunk
                if chunk['id'] not in image_cache:
                    if len(image_cache) >= 4: 
                        image_cache.pop(next(iter(image_cache)))
                    
                    # Canvas size accommodates rock + text margin
                    canvas = np.zeros((chunk['virtual_h'], ROCK_WIDTH + margin_w, 3), dtype=np.uint8)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    
                    if chunk['type'] == 'core':
                        raw_img = cv2.imread(chunk['path'])
                        scaled_img = cv2.resize(raw_img, (ROCK_WIDTH, chunk['virtual_h']), interpolation=cv2.INTER_LANCZOS4)
                        canvas[:, margin_w:] = scaled_img
                        
                        if depth_mode:
                            # DYNAMIC COORDINATES: Shift drawing direction based on Zoom level
                            if margin_w > 0:
                                # Zoom > 1.0: Draw ticks left into the black margin
                                tick_start = margin_w
                                tick_end_major = margin_w - 35
                                tick_end_minor = margin_w - 15
                                text_x = 10
                            else:
                                # Zoom 1.0: Draw ticks right into the rock face
                                tick_start = 0
                                tick_end_major = 35
                                tick_end_minor = 15
                                text_x = 45 # Push text to the right of the tick marks
                            
                            # Auto-detect if we are in meters or feet based on user input
                            is_metric = unit.strip().lower().startswith('m')
                            major_step = 0.1 if is_metric else 1.0   
                            minor_step = 0.01 if is_metric else 0.1  
                            
                            top_d = chunk['top']
                            bot_d = chunk['bot']
                            
                            if bot_d > top_d: 
                                start_d = math.ceil((top_d - 1e-5) / minor_step) * minor_step
                                current_d = round(start_d, 3)
                                
                                while current_d <= bot_d + 1e-5:
                                    y = int((current_d - top_d) / (bot_d - top_d) * chunk['virtual_h'])
                                    
                                    remainder = abs(current_d) % major_step
                                    is_major = remainder < 1e-4 or abs(major_step - remainder) < 1e-4
                                    
                                    if is_major:
                                        # Major Tick
                                        cv2.line(canvas, (tick_end_major, y), (tick_start, y), (255, 255, 255), MAJOR_TICK_THICKNESS)
                                        
                                        if is_metric:
                                            label_val = f"{current_d:.{DECIMAL_PLACES_METRIC}f}"
                                        else:
                                            label_val = f"{current_d:.{DECIMAL_PLACES_FEET}f}"
                                            
                                        y_offset = int(FONT_SCALE * 10)
                                        full_label = f"{label_val}{unit}"
                                        
                                        # --- TEXT STROKE EFFECT ---
                                        # 1. Draw thick black outline underneath
                                        cv2.putText(canvas, full_label, (text_x, y + y_offset), font, FONT_SCALE, (0, 0, 0), FONT_THICKNESS + 3)
                                        # 2. Draw standard white text on top
                                        cv2.putText(canvas, full_label, (text_x, y + y_offset), font, FONT_SCALE, (200, 200, 200), FONT_THICKNESS)
                                    else:
                                        # Minor Tick
                                        cv2.line(canvas, (tick_end_minor, y), (tick_start, y), (255, 255, 255), MINOR_TICK_THICKNESS)
                                        
                                    current_d += minor_step
                                    current_d = round(current_d, 3) 
                            
                    elif chunk['type'] == 'gap':
                        # Draw Gap Block Notification
                        gap_font_scale = FONT_SCALE + 0.1
                        cv2.putText(canvas, "MISSING INTERVAL", (10, chunk['virtual_h']//2 - 20), font, gap_font_scale, (0, 0, 255), FONT_THICKNESS)
                        cv2.putText(canvas, f"{chunk['top']}{unit} to {chunk['bot']}{unit}", (10, chunk['virtual_h']//2 + 20), font, gap_font_scale, (0, 0, 255), FONT_THICKNESS)
                        
                    image_cache[chunk['id']] = canvas
                
                cached_img = image_cache[chunk['id']]
                crop = cached_img[local_v_start:local_v_end, :]
                frame_pieces.append(crop)
                    
        # Assemble the final view
        if frame_pieces:
            composite_column = cv2.vconcat(frame_pieces)
            if composite_column.shape[0] != HEIGHT:
                composite_column = cv2.resize(composite_column, (ROCK_WIDTH + margin_w, HEIGHT))
        else:
            composite_column = np.zeros((HEIGHT, ROCK_WIDTH + margin_w, 3), dtype=np.uint8)

        # Build Final Centered Frame
        final_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        
        # Calculate X position so the ROCK is perfectly centered, regardless of the text margin
        place_x_start = X_OFFSET - margin_w
        place_x_end = X_OFFSET + ROCK_WIDTH
        final_frame[:, place_x_start : place_x_end] = composite_column

        video_writer.write(final_frame)

        if i % 60 == 0:
            print(f"  Progress: {int(progress * 100)}%")

    video_writer.release()
    print(f"Success! Video saved to: {output_path}")

if __name__ == "__main__":
    create_core_video_direct_stream()


# In[ ]:




