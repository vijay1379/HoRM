# Logo Instructions

## Adding Your Company Logo

To add your company logo to the website:

1. **Place your logo file** in the following location:
   ```
   static/images/logo.png
   ```

2. **Supported formats:**
   - PNG (recommended for transparency)
   - JPG/JPEG
   - SVG
   - WebP

3. **Recommended dimensions:**
   - **For navbar**: 150x32 pixels (wide logo replacing text)
   - **For login page**: 120x40 pixels (wide logo replacing text)
   - **Format**: Rectangular logo that replaces the "AttendanceAnalyzer" text
   - **Aspect ratio**: Approximately 4:1 or 3:1 (width:height)

4. **File naming:**
   - Name your logo file as `logo.png` (or `logo.jpg`, `logo.svg`)
   - If using a different name/format, update the HTML files:
     ```html
     <!-- Change this line in both login.html and index.html -->
     <img src="{{ url_for('static', filename='images/your-logo-name.png') }}" ...>
     ```

## Current Logo Implementation

The logo is currently added to:
- ✅ **Landing page navbar** (index.html) - 150x32 pixels (replaces "AttendanceAnalyzer" text)
- ✅ **Login page header** (login.html) - 120x40 pixels (replaces "AttendanceAnalyzer" text)

## CSS Styling

The logo includes:
- Smooth hover effects
- Proper alignment with text
- Responsive scaling
- Rounded corners
- Professional transitions

## Alternative Options

If you don't have a logo yet, you can:
1. Keep the current Font Awesome icon
2. Use a text-based logo
3. Create a simple logo using online tools like Canva or LogoMaker

---

**Note:** Simply replace this README file with your actual logo image named `logo.png` in the same directory.