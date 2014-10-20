Production run time:

# Create a new screen session for production running
# This is not the ideal production environment, writing an init script for this would be better
screen -S prod

# Elevate to root user
sudo su - 

# Change to the project's working directory and activate the Python virtual environment
cd /opt/inspector/inspector/
source ../env/bin/activate

# Run the WSGI server with it's production config file
gunicorn --paste production.ini

# Create a new screen window
# Press CTRL+a then c
cd /opt/inspector/inspector/
source ../env/bin/activate

# Run the celery workers
pceleryd production.ini

# At this point, you may safely disconnect from the screen session
