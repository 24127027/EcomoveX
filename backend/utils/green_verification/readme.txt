This module requires python 3.10 
and the following dependencies defined in the requirements.txt file in the same directory.

This module will be deploy as a separate service
in Render and communicate with the main backend via 
REST API calls.

To set up the environment, you can use the following commands:
# uv will automatically download Python 3.10 if not installed
uv python install 3.10
# Then create the venv
uv venv venv-py310 --python 3.10
# Activate the venv
uv venv activate venv-py310
# Install dependencies
uv pip install -r backend/utils/green_verification/requirements.txt
