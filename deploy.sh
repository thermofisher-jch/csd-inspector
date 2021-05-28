#!/usr/bin/env bash
# Builds an image, tags buildtime tag and others as specified, then pushes to a container repository

set -e

readonly IMAGE_REGISTRY="vulcan.itw:5000"

# Default values
deploy_host=""
deploy_version=""

print_usage() {
    echo "Depploys a tagged version to a repository"
    echo
    echo "Usage:"
    echo "  bash deploy.sh -s <hostname> -t <version_tag>"
    echo
    echo "Options:"
    echo "  -s <hostname>: Name of image, relative to project namespace.  Required"
    echo "  -t <version_tag>: Version to deploy"
}

while getopts 's:t:h:' flag; do
    case "${flag}" in
    s) readonly deploy_host="${OPTARG}" ;;
    t) readonly deploy_version="${OPTARG}" ;;
    h)
        print_usage
        exit 0
        ;;
    *)
        print_usage
        exit 1
        ;;
    esac
done

echo "TODO: Verify that I am logged in to the docker registry here"


if [[ ! "${deploy_host}" ]]; then
    echo "Missing required deployment host name"
    print_usage
    exit 1
fi

if [[ ! "${deploy_version}" ]]; then
    echo "Missing required deployment tag name"
    print_usage
    exit 1
fi

export DOCKER_HOST="ssh://${deploy_host}"
export VERSION="${deploy_version}"
docker-compose -f docker-compose.prod.yml -f docker-compose.yml rm -f -s django celery nginx
docker-compose -f docker-compose.prod.yml -f docker-compose.yml up -d &

