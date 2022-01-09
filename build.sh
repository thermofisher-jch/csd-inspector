#!/usr/bin/env bash
# Builds an image, tags with buildtime tag and additional requested tags, then pushes to development container repository

set -e

readonly IMAGE_REGISTRY="vulcan.itw:5000"

# Default values
build_context_arg="."
dockerfile_arg=""
project_namespace=""
image_name=""
extra_tags_arg="latest"
image_tag="$(whoami)-$(date +%Y%m%d_%H%M%S)"
add_local_dev=0
add_latest=0
add_githash=0

print_usage() {
    echo "Builds an image, tags with buildtime tag and additional requested tags, then pushes to development container repository"
    echo
    echo "Usage:"
    echo "  bash build.sh -c <build_context> -f <docker_file> -i <image_name> -t <extra_tag,more_extra_tags> -- [<other docker build args>]"
    echo
    echo "Options:"
    echo "  -c <build_context>: Path to context root.  Defaults to current directory."
    echo "  -f <docker_file>: Path to docker file.  Defaults to <build_context>/Dockerfile"
    echo "  -i <image_name>: Name of image, relative to project namespace.  Required"
    echo "  -n <project_namespace>: Project namespace image is tagged under.  Optional."
    echo "  -t <image_tags>: Comma separated addtional tags.  Defaults to 'latest'"
    echo "  -D : Shorthand to add 'local-dev' tag"
    echo "  -L : Shorthand to add 'latest' tag"
    echo "  -G : Add git commit hash tag"
}

while getopts 'c:f:i:n:t:DLGh:' flag; do
    case "${flag}" in
    c) readonly build_context_arg="${OPTARG}" ;;
    f) readonly dockerfile_path_arg="${OPTARG}" ;;
    i) readonly image_name="${OPTARG}" ;;
    n) readonly project_namespace="${OPTARG}" ;;
    t) readonly extra_tags_arg="${OPTARG}" ;;
    D) readonly add_local_dev=1 ;;
    L) readonly add_latest=1 ;;
    G) readonly add_githash=1 ;;
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

if [[ ! "${build_context_arg}" ]]; then
    readonly build_context=$(pwd)
else
    readonly build_context="${build_context_arg}"
fi

if [[ ! -d "${build_context}" ]]; then
    echo "Build context must be a directory"
    print_usage
    exit 1
fi

if [[ ! "${dockerfile_path_arg}" ]]; then
    readonly dockerfile_path="${build_context}/Dockerfile"
else
    readonly dockerfile_path="${dockerfile_path_arg}"
fi

if [[ ! -f "${dockerfile_path}" ]]; then
    echo "Dockerfile path must be a file"
    print_usage
    exit 1
fi
# if [[ ! "${extra_tags_arg}" ]]; then
#     readonly extra_tags=local-dev
# fi


if [[ ! ${project_namespace} ]]; then
	readonly full_untagged_name="${IMAGE_REGISTRY}/${image_name}"
	readonly full_tagged_name="${IMAGE_REGISTRY}/${image_name}:${image_tag}"
else
	readonly full_untagged_name="${IMAGE_REGISTRY}/${project_namespace}/${image_name}"
	readonly full_tagged_name="${IMAGE_REGISTRY}/${project_namespace}/${image_name}:${image_tag}"
fi

shift "$((OPTIND - 1))" # Remaining args are sent to `docker build` (or `podman build`)
if command -v buildah > /dev/null; then
    # Jenkins uses buildah instead of docker because of the complexity of building an
    # image inside another image.
    # buildah login --username ${username} --password "$(oc whoami -t)" "${IMAGE_REGISTRY}"
    buildah build --tag "${full_tagged_name}" -f "${dockerfile_path}" "$@" "${build_context}/."
    # buildah push "${full_tagged_name}"
    build_cmd="buildah"
else
    # docker login --username ${username} --password "${password}" "${IMAGE_REGISTRY}"
    docker build --tag "${full_tagged_name}" -f "${dockerfile_path}" "$@" "${build_context}/."
    # docker push "${full_tagged_name}"
    build_cmd="docker"
fi

IFS="," read -ra arr <<< "${extra_tags_arg}"

# Print each value of the array by using the loop
for extra_tag in "${arr[@]}";
do
	echo "Adding ${extra_tag} tag"

	${build_cmd} tag "${full_tagged_name}" "${full_untagged_name}:${extra_tag}"
	# ${build_cmd} push "${full_untagged_name}:${extra_tag}"

	if [[ "x${extra_tag}" == "xlatest" ]]; then
		add_latest=0
	fi
done

if [[ ${add_local_dev} -eq 1 ]]; then
	echo "Adding local-dev tag"

	${build_cmd} tag "${full_tagged_name}" "${full_untagged_name}:local-dev"
fi

if [[ ${add_latest} -eq 1 ]]; then
	echo "Adding latest tag"

	${build_cmd} tag "${full_tagged_name}" "${full_untagged_name}:latest"
	# ${build_cmd} push "${full_untagged_name}:latest"
fi

if [[ ${add_githash} -eq 1 ]]; then
	githash=$(git rev-parse --short --verify HEAD)
	extra_tag="githash-${githash}"
	echo "Adding ${extra_tag} tag"

	${build_cmd} tag "${full_tagged_name}" "${full_untagged_name}:${extra_tag}"
	# ${build_cmd} push "${full_untagged_name}:${extra_tag}"
fi
	
echo "Done!"
