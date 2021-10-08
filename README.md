# vManagerGUI
Web GUI for basic SDWAN operations tasks.  Currently supports:
- Deploy a New Edge
- Change Edge Template Values
- RMA an Edge (Hardware Replacement)
- List Edges
- List Templates

Runs as a Python3 Flask app natively for testing.  Tested on GCP and Apache for production.

# Screenshots
Menu Screenshot:

![ScreenShotMenu](https://user-images.githubusercontent.com/46031546/136489458-3c5da362-9e20-48b9-9be7-5ad42ba16519.png)

Edit or Deploy a Device Screenshot:

![ScreenShotEdit](https://user-images.githubusercontent.com/46031546/136489454-385b339a-b5b6-46ac-be81-7153ce7eb8e7.png)

# Basic use instructions:
- Clone repository

    `git clone https://github.com/dbrown92700/vManagerGUI`
- Change to directory and create a virtual environment

    `cd vManagerGUI`
    
    `python3 -m venv env`
    
    `source env/bin/activate`
- Install python libraries

    `pip install -r requirements.txt`
- Execute the app

    `python3 main.py`
- Browse to the local webserver

    `http://localhost:8080`

This project was written and is maintained by the following individuals:

## Author

* David Brown <davibrow@cisco.com>
