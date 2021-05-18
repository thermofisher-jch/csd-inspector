#!/usr/bin/env bash
# Builds an image, tags buildtime tag and others as specified, then pushes to a container repository

set -e

readonly IMAGE_REGISTRY="vulcan.itw:5000"

# Default values
project_namespace=""
image_name=""

print_usage() {
    echo "Publishes tag additions to a repository"
    echo
    echo "Usage:"
    echo "  bash publish -i <image_name> [-n <project_namespace>] [ -s <source tag> ] -d <published tag>"
    echo
    echo "Options:"
    echo "  -i <image_name>: Name of image, relative to project namespace.  Required"
    echo "  -n <project_namespace>: Project namespace image is tagged under.  Optional."
    echo "  -s <source_tags>: Defaults to 'latest'"
    echo "  -d <published_tags>: Required"
}

while getopts 'i:n:s:d:h:' flag; do
    case "${flag}" in
    i) readonly image_name="${OPTARG}" ;;
    n) readonly project_namespace="${OPTARG}" ;;
    s) readonly source_tag_arg="${OPTARG}" ;;
    d) readonly publish_tag="${OPTARG}" ;;
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


if [[ ! "${image_name}" ]]; then
    echo "Missing required image name"
    print_usage
    exit 1
fi

if [[ ! "${source_tag_arg}" ]]; then
    readonly source_tag="latest"
else
    readonly source_tag="${source_tag_arg}"
fi

if [[ ! "${publish_tag}" ]]; then
    echo "Publish tag is required"
    exit 1
fi


if [[ ! ${project_namespace} ]]; then
	readonly source_tagged_name="${IMAGE_REGISTRY}/${image_name}:${source_tag}"
	readonly publish_tagged_name="${IMAGE_REGISTRY}/${image_name}:${publish_tag}"
else
	readonly source_tagged_name="${IMAGE_REGISTRY}/${project_namespace}/${image_name}:${source_tag}"
	readonly publish_tagged_name="${IMAGE_REGISTRY}/${project_namespace}/${image_name}:${publish_tag}"
fi

if command -v buildah > /dev/null; then
    # Jenkins uses buildah instead of docker because of the complexity of building an
    # image inside another image.
    # buildah login --username ${username} --password "$(oc whoami -t)" "${IMAGE_REGISTRY}"
    build_cmd="buildah"
else
    # docker login --username ${username} --password "${password}" "${IMAGE_REGISTRY}"
    build_cmd="docker"
fi
"${build_cmd}" tag "${source_tagged_name}" "${publish_tagged_name}"
"${build_cmd}" push "${publish_tagged_name}"
	
echo "Done!"
