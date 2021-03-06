# Cisco SDWAN Ops GUI   [![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/CiscoSE/vManageOpsGUI)

Web GUI for basic SD-WAN operations tasks.  Currently supports:
- Deploy a New Edge
- Change Edge Template Values
- RMA an Edge (Hardware Replacement)
- List Edges
- List Templates

Runs as a Python3 Flask app natively for testing.  Tested on GCP and Apache for production.

# Screenshots
### Menu Screenshot:
![menu](https://user-images.githubusercontent.com/46031546/145484379-9c11be71-65b9-4a50-a149-7ee440a015d0.png)

------

### Edit or Deploy a Device Screenshot:
![ScreenShotEdit](https://user-images.githubusercontent.com/46031546/136489454-385b339a-b5b6-46ac-be81-7153ce7eb8e7.png) 
------

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
    
# Testing

Test the app using the Cisco Sandboxes at https://developer.cisco.com/sdwan/sandbox/
- The **ALWAYS-ON SANDBOX** Sandbox is restricted to Read Only and will generate errors in the later steps of the deploy, change config or RMA workflows.
- The **RESERVATION SANDBOX** works fully with all workflows

## Author

This project was written and is maintained by the following individuals:

* David Brown <davibrow@cisco.com>

