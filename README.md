## Host
Ubuntu: 14.04+

## Dependencies
Install fabric on your machine: http://www.fabfile.org/installing.html
Docker: https://www.docker.com/
Docker Compose: https://docs.docker.com/compose/

## Development

Run `fab dev` from this directory.

## Tests

Run all tests with `fab test` from this directory.
Run one test with `fab test:IonInspector.reports.tests.test_Chef_Kit_Details.ChefChipTestCase` from this directory.

## Deployment

Commit and push your changes to this repository.

### To Testing (inspector.vulcan.itw)

Run `fab deploy:<tag name> -H jarvis.itw` from this directory.

### Old Production Deployment (for reference) 


    Production run time:
    
    Create a new screen session for production running
    This is not the ideal production environment, writing an init script for this would be better
    screen -S prod
    
    Elevate to root user
    sudo su - 
    
    Change to the project's working directory
    cd /opt/inspector/inspector/
    
    activate the Python virtual environment
    source ../env/bin/activate
    
    Run the WSGI server with it's production config file
    gunicorn --paste production.ini
    
    Create a new screen window
    screen
    
    Elevate to root user and activate virtual env again
    sudo su - 
    cd /opt/inspector/inspector/
    source ../env/bin/activate
    
    Run the celery workers
    pceleryd production.ini
    
    At this point, you may safely detach from the screen session
