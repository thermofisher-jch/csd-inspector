#!/bin/bash
# Add a more recent version of erlang to the repos
wget -O /etc/yum.repos.d/epel-erlang.repo http://repos.fedorapeople.org/repos/peter/erlang/epel-erlang.repo
# Add the package signing key for the more recent verison of RabbitMQ packaged by the authors
rpm --import http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
# Download that more recent version
wget https://www.rabbitmq.com/releases/rabbitmq-server/v2.8.2/rabbitmq-server-2.8.2-1.noarch.rpm
# Get the info the the new Erlang repo
yum update
# Install it
yum install erlang
yum install rabbitmq-server-2.8.2-1.noarch.rpm
# Enable automatic boot of rabbitmq by default
chkconfig rabbitmq-server on
/etc/init.d/rabbitmq-server start
rabbitmqctl add_vhost lemon
rabbitmqctl add_user lemon lemonpass
rabbitmqctl set_permissions -p lemon lemon ".*" ".*" ".*"
