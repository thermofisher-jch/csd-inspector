## Development
Install vagrant on your machine: http://docs.vagrantup.com/v2/installation/index.html

Run `vagrant up` from this directory.

You can copy the production db to the local machine by running `fabric clone_db` on the local machine.
Unlike `fab deploy`, you would run this either on sherlock.itw or inside your vagrant vm.

TODO: Make `fabric clone_db` copy some filesystem data.

## Deployment
Install ansible on your machine: http://docs.ansible.com/ansible/intro_installation.html

Install fabric on your machine: http://www.fabfile.org/installing.html

Commit and push your changes to this repository.

### To Testing (sherlock.itw)
Copy your public key to sherlock.itw: `ssh-copy-id ionadmin@sherlock.itw`

Run `fab deploy:testing` from this directory.
    
### To Production (inspector.itw)
Copy your public key to inspector.itw: `ssh-copy-id ionadmin@inspector.itw`

Run `fab deploy` from this directory. 

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
