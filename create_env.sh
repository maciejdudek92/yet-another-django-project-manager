create_venv() {
    local env_name=${1:-"venvaa"}

    if [ -d "$env_name" ]; then
        echo "Virtual environment '$env_name' already exists. Aborting."
        return 1
    fi

    python3 -m venv "$env_name"
    source "./$env_name/bin/activate"
    pip install -U pip
}
activate_venv() {
    local env_name=${1:-".venv"}

    if [ ! -d "$env_name" ]; then
        echo "Virtual environment '$env_name' not found. Use '$0 create [env_name]' to create one."
        return 1
    fi

    source "./$env_name/bin/activate"
}

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_help
    return 0
fi

case "$1" in
    "create")
        create_venv "$2"
        ;;
    "activate")
        activate_venv "$2"
        ;;
    *)
        echo "Unknown option: $1"
        print_help
        exit 1
        ;;
esac