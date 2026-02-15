How to Run This Tool (No Coding Experience Required)



These scripts are designed to process large image files, so it is best run this script locally on your own computer. There are many tutorials that explain in detail how to set up python on your computer, but a very quick and simple method is listed below.  



&nbsp;



Step 1: Get the "Engine" (Python) You need Python installed to run the script.



There are many detailed instructional tutorials explaining how to set up Python on your computer. Two popular options are listed below.



&nbsp;



Method 1: Using Pip (Recommended for lightweight installation) 



Install Python: Download and install the latest Python from python.org. Ensure "Add Python to PATH" is checked during installation.

Open Command Prompt: Search for cmd in the Windows search bar.

Install Jupyter: Type the following command and press Enter:

pip install notebook

Run Jupyter: Type jupyter notebook in the command prompt to start. 

&nbsp;



Method 2: Using Anaconda (Recommended for Data Science) 



Download Anaconda: Download the Anaconda installer for Windows.

Install: Run the .exe file and follow the on-screen instructions.

Launch Jupyter: Open the Anaconda Prompt and type jupyter notebook. 

&nbsp;



Step 2: Get the Tool



Go to the GeoPhoto-Tools Repository.

Click the green <> Code button and select Download ZIP.

Extract the ZIP folder to somewhere easy to find (like your Desktop).

&nbsp;



Step 3: Install the "Drivers" (Libraries) The script uses a few specialized tools to handle large files.



Open your computer's Command Prompt (search for "cmd" in the Windows start menu).

Paste this line into the black window and hit Enter:



pip install rawpy imageio imageio\[ffmpeg] exifread numpy opencv-python earthengine-api



(You will see some text scroll by. Once it stops and shows the cursor again, it's done).



Install Hugin (https://hugin.sourceforge.io/download/)

&nbsp;



Step 4: Load the code



Open the program you with to run in your preferred Python application (installed during step 1). Open the \*.ipynb file for jupyter notebook or \*.py file for of python compilers.

Read the detailed notes and then edit “ USER CONFIGURATION “ lines to assign run variables.

&nbsp;



Step 5: Run

