#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Core Segment Stitcher


# In[ ]:


"""
=============================================================================
Core Segment Stitcher
=============================================================================
Description:
    A graphical user interface (GUI) tool designed to extract vertical core 
    segments from core box photos and stitch them end-to-end into a 
    single, continuous high-resolution vertical column. 

Prerequisites:
    pip install opencv-python Pillow numpy

Usage Instructions:
    1. Run the script. A folder selection dialog will appear.
    2. Select the folder containing your core box photos.
    3. Enter the number of core segments (columns) present in each box.
    4. The first image will load with yellow bounding boxes. 
       - Click and drag the EDGES of the boxes to resize them.
       - Click and drag the CENTER of a box to move it.
    5. Press [SPACEBAR] to extract, stitch, save, and load the next photo.
    6. Press [ESCAPE] to quit the application at any time.

Output:
    Saves stitched images to a "Stitched_Output" subfolder within the 
    original image directory.

    Hint: it is better to use file names that sort from bottom of core to top 
    so the output stripes are in order, but the code processes core box photos
    one by one in any order that the yare arranged in your folder.
=============================================================================
"""
import os
import glob
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

class CoreStitcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Core Segment Stitcher")
        
        # Setup state variables
        self.image_paths = []
        self.current_idx = 0
        self.num_segments = 0
        self.boxes = [] 
        self.scale_factor = 1.0
        self.original_cv_image = None
        
        # --- Memory variable to hold coordinates ---
        self.saved_box_coords = None 
        
        # Dragging state
        self.selected_box = None
        self.drag_mode = None 
        self.start_x = 0
        self.start_y = 0

        # UI Setup
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<space>", self.process_and_next)
        self.root.bind("<Escape>", self.quit_app)

        # Start workflow
        self.root.after(100, self.init_workflow)

    def init_workflow(self):
        folder = filedialog.askdirectory(title="Select Folder containing Core Photos")
        if not folder:
            self.root.destroy()
            return
            
       # Grab files and prevent Windows from duplicating them
        valid_extensions = ('.jpg', '.jpeg', '.png')
        for filename in os.listdir(folder):
            if filename.lower().endswith(valid_extensions):
                self.image_paths.append(os.path.join(folder, filename))
                
        # Sort alphabetically so they process in perfect sequence (Box1, Box2...)
        self.image_paths.sort()
            
        if not self.image_paths:
            messagebox.showerror("Error", "No images found in the selected folder.")
            self.root.destroy()
            return
            
        self.num_segments = simpledialog.askinteger("Input", "Number of core segments per photo (n):", minvalue=1, maxvalue=20)
        if not self.num_segments:
            self.root.destroy()
            return
            
        self.output_dir = os.path.join(folder, "Stitched_Output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.load_image()

    def load_image(self):
        if self.current_idx >= len(self.image_paths):
            messagebox.showinfo("Done", "All images processed!")
            self.root.destroy()
            return

        img_path = self.image_paths[self.current_idx]
        self.root.title(f"Processing ({self.current_idx + 1}/{len(self.image_paths)}): {os.path.basename(img_path)} - [SPACE] to Save&Next | [ESC] to Quit")
        
        self.original_cv_image = cv2.imread(img_path)
        orig_h, orig_w = self.original_cv_image.shape[:2]
        
        img_rgb = cv2.cvtColor(self.original_cv_image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        max_display_height = 900
        self.scale_factor = max_display_height / orig_h
        new_w = int(orig_w * self.scale_factor)
        new_h = int(orig_h * self.scale_factor)
        
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(pil_img)
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))
        
        self.init_boxes(new_w, new_h)

    def init_boxes(self, w, h):
        self.boxes.clear()
        
        # Check for memory before drawing
        if self.saved_box_coords:
            for i, coords in enumerate(self.saved_box_coords):
                x1, y1, x2, y2 = coords
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="yellow", width=3)
                label = self.canvas.create_text(x1 + 15, y1 + 15, text=str(i+1), fill="yellow", font=("Arial", 16, "bold"))
                self.boxes.append({'id': rect, 'label': label, 'coords': [x1, y1, x2, y2]})
        else:
            col_width = w / self.num_segments
            margin = 10
            y1 = int(h * 0.25)
            y2 = int(h * 0.75)
            
            for i in range(self.num_segments):
                x1 = (i * col_width) + margin
                x2 = ((i + 1) * col_width) - margin
                
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="yellow", width=3)
                label = self.canvas.create_text(x1 + 15, y1 + 15, text=str(i+1), fill="yellow", font=("Arial", 16, "bold"))
                self.boxes.append({'id': rect, 'label': label, 'coords': [x1, y1, x2, y2]})

    def on_press(self, event):
        x, y = event.x, event.y
        self.selected_box = None
        self.drag_mode = None
        tolerance = 15 
        
        for box in self.boxes:
            bx1, by1, bx2, by2 = box['coords']
            if abs(x - bx1) < tolerance and by1 < y < by2:
                self.drag_mode = 'left'
            elif abs(x - bx2) < tolerance and by1 < y < by2:
                self.drag_mode = 'right'
            elif abs(y - by1) < tolerance and bx1 < x < bx2:
                self.drag_mode = 'top'
            elif abs(y - by2) < tolerance and bx1 < x < bx2:
                self.drag_mode = 'bottom'
            elif bx1 < x < bx2 and by1 < y < by2:
                self.drag_mode = 'move'
                
            if self.drag_mode:
                self.selected_box = box
                self.start_x = x
                self.start_y = y
                break

    def on_drag(self, event):
        if not self.selected_box: return
        
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        coords = self.selected_box['coords']
        
        if self.drag_mode == 'left':   coords[0] += dx
        elif self.drag_mode == 'right':  coords[2] += dx
        elif self.drag_mode == 'top':    coords[1] += dy
        elif self.drag_mode == 'bottom': coords[3] += dy
        elif self.drag_mode == 'move':
            coords[0] += dx; coords[2] += dx
            coords[1] += dy; coords[3] += dy
            
        self.canvas.coords(self.selected_box['id'], *coords)
        self.canvas.coords(self.selected_box['label'], coords[0] + 15, coords[1] + 15)
        
        self.start_x = event.x
        self.start_y = event.y

    def process_and_next(self, event=None):
        print("Stitching segments...")
        
        # --- Commit current box coordinates to memory BEFORE moving on ---
        self.saved_box_coords = [box['coords'].copy() for box in self.boxes]
        
        segments = []
        sorted_boxes = sorted(self.boxes, key=lambda b: int(self.canvas.itemcget(b['label'], 'text')))
        
        for box in sorted_boxes:
            bx1, by1, bx2, by2 = [int(c / self.scale_factor) for c in box['coords']]
            bx1, by1 = max(0, bx1), max(0, by1)
            bx2 = min(self.original_cv_image.shape[1], bx2)
            by2 = min(self.original_cv_image.shape[0], by2)
            
            segment = self.original_cv_image[by1:by2, bx1:bx2]
            segments.append(segment)
            
        # Ensure widths are identical by padding with black space on the right
        max_width = max(seg.shape[1] for seg in segments)
        padded_segments = []
        for seg in segments:
            if seg.shape[1] < max_width:
                padding = np.zeros((seg.shape[0], max_width - seg.shape[1], 3), dtype=np.uint8)
                seg = np.hstack((seg, padding))
            padded_segments.append(seg)
            
        final_stitched = cv2.vconcat(padded_segments)
        
        orig_filename = os.path.basename(self.image_paths[self.current_idx])
        name, ext = os.path.splitext(orig_filename)
        save_path = os.path.join(self.output_dir, f"{name}_stitched{ext}")
        cv2.imwrite(save_path, final_stitched)
        
        self.current_idx += 1
        self.load_image()

    def quit_app(self, event=None):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-topmost', True)  # Forces it to the absolute front
    root.attributes('-topmost', False) # Instantly turns the lock off so you can still minimize it later
    root.state('zoomed') 
    app = CoreStitcherApp(root)
    root.mainloop()


# In[ ]:




