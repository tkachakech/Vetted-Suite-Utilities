import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont
import os
import sys

class ProWatermarkTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Document Watermarker (Tiled)")
        self.root.geometry("500x550")
        
        # --- KILL THE FEATHER (NUITKA COMPATIBLE) ---
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "app_icon.ico")
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon Load Failed: {e}")
        
        self.image_paths = []
        
        # --- UI SETUP ---
        tk.Label(self.root, text="1. Choose Documents", font=("Arial", 10, "bold")).pack(pady=(15, 0))
        tk.Button(self.root, text="Browse Images (Multi-Select)", command=self.select_images).pack(pady=5)
        self.file_label = tk.Label(self.root, text="0 files selected", fg="gray")
        self.file_label.pack()
        
        tk.Label(self.root, text="2. Watermark Text", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        self.text_entry = tk.Entry(self.root, width=55)
        self.text_entry.insert(0, "type your watermark message here")
        self.text_entry.pack()
        
        # INCREASED DEFAULT OPACITY TO 150 FOR DEBUGGING
        self.opacity_slider = self.create_setting(
            "Opacity (Transparency)", 0, 255, 150,
            "0 = Invisible\n255 = Solid text\n\nDefaulted to 150 so you can clearly see it working!"
        )
        
        self.angle_slider = self.create_setting(
            "Text Angle (Orientation)", -90, 90, 45,
            "Controls the tilt of the watermark."
        )
        
        self.density_slider = self.create_setting(
            "Pattern Density (Frequency)", 1, 10, 6,
            "Controls how many times the watermark repeats across the page.\n\n"
            "• Low (1-3): Fewer repetitions with large gaps. Best for keeping the document very easy to read.\n"
            "• High (8-10): Tightly packed 'wallpaper' pattern. Best for security, as it ensures the watermark "
            "covers every part of the document, making it much harder to tamper with."
        )
        
        
        tk.Button(self.root, text="Apply to All & Save", command=self.apply_watermark, 
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), padx=20, pady=5).pack(pady=25)

    def create_setting(self, title, min_val, max_val, default_val, help_text):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=30, pady=(15, 0))
        
        top_row = tk.Frame(frame)
        top_row.pack(fill="x")
        tk.Label(top_row, text=title, font=("Arial", 9, "bold")).pack(side="left")
        
        help_btn = tk.Button(top_row, text=" [ ? ] ", relief="flat", fg="#0066cc", cursor="hand2",
                             command=lambda: messagebox.showinfo(f"Help: {title}", help_text))
        help_btn.pack(side="left", padx=5)
        
        slider = tk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL)
        slider.set(default_val)
        slider.pack(fill="x")
        return slider

    def select_images(self):
        filepaths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if filepaths:
            self.image_paths = list(filepaths)
            self.file_label.config(text=f"{len(self.image_paths)} files selected")

    def apply_watermark(self):
        if not self.image_paths:
            messagebox.showwarning("Warning", "Please select at least one image.")
            return
            
        text = self.text_entry.get()
        if not text:
            messagebox.showwarning("Warning", "Please enter watermark text.")
            return

        save_dir = filedialog.askdirectory(title="Select Output Folder")
        if not save_dir:
            return

        success_count = 0
        
        opacity = self.opacity_slider.get()
        angle = self.angle_slider.get()
        density = self.density_slider.get()
        
        for path in self.image_paths:
            try:
                base_image = Image.open(path).convert("RGBA")
                width, height = base_image.size
                
                text_layer = Image.new("RGBA", (width, height), (255, 255, 255, 0))
                font_size = max(int(width / 35), 20) 
                
                # Robust Font Loading
                try:
                    font = ImageFont.truetype("arial.ttf", font_size) 
                except IOError:
                    try:
                        font = ImageFont.load_default(size=font_size) 
                    except:
                        font = ImageFont.load_default() 
                
                dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
                bbox = dummy_draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                
                txt_img = Image.new("RGBA", (tw, th), (255, 255, 255, 0))
                txt_draw = ImageDraw.Draw(txt_img)
                
                # CHANGED: Color is now pure Black (0,0,0) for maximum contrast
                txt_draw.text((-bbox[0], -bbox[1]), text, font=font, fill=(0, 0, 0, opacity))
                
                rotated_txt = txt_img.rotate(angle, expand=True)
                rtw, rth = rotated_txt.size
                
                gap_multiplier = 2.5 - (density * 0.2) 
                step_x = int(rtw * gap_multiplier) + 50
                step_y = int(rth * gap_multiplier) + 50
                
                for x in range(-rtw, width + rtw, step_x):
                    row_count = 0
                    for y in range(-rth, height + rth, step_y):
                        offset_x = int(step_x / 2) if row_count % 2 != 0 else 0
                        text_layer.paste(rotated_txt, (x + offset_x, y), rotated_txt)
                        row_count += 1
                
                watermarked_image = Image.alpha_composite(base_image, text_layer)
                
                filename = os.path.basename(path)
                name, ext = os.path.splitext(filename)
                save_path = os.path.join(save_dir, f"{name}_watermarked.jpg")
                
                rgb_image = watermarked_image.convert("RGB")
                rgb_image.save(save_path, quality=95)
                success_count += 1
                
            except Exception as e:
                # CHANGED: Explicit error popup so it cannot fail silently!
                messagebox.showerror("Crash Report", f"Failed on file: {os.path.basename(path)}\n\nError details: {str(e)}")
                
        if success_count > 0:
            messagebox.showinfo("Success", f"Successfully watermarked {success_count} files.\n\nPlease check the folder you just selected to view them.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProWatermarkTool(root)
    root.mainloop()
