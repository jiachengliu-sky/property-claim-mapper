import sys
import os
from streamlit.web import cli as stcli

def main():
    # Set the path to the app.py file relative to the executable
    if getattr(sys, 'frozen', False):
        # If running as an executable
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    app_path = os.path.join(base_path, "app.py")
    
    # Set the command line arguments for streamlit
    sys.argv = [
        "streamlit", 
        "run", 
        app_path, 
        "--global.developmentMode=false",
    ]
    
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
