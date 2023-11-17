#!/bin/bash

retrieve_tokens() {
    mkdir -p ./.temp_git/
    git clone git@github.com:Johnsn0w/token_discord.git ./.temp_git/
    mv ./.temp_git/.env ./mr_robot/
    rm -rf ./.temp_git/
}

# cmdline_arg=$1 # store cmdline arg to variable

# case $cmdline_arg in # switch case for command line arguement
#     "run")  # "run" docker compose normally
#         docker compose up -d
#         ;;
#     "run_and_update") # "run_and_update" docker compose and update
#         git -C /bot_overlord pull
#         docker compose -f /bot_overlord/docker-compose.yml up -d --build
#         ;;
#     "run_clean_slate") # "run_clean_slate" docker compose on a clean slate (purge all containers, images, and cache but not volumes)
#         docker compose -f /bot_overlord/docker-compose.yml down --rmi all --volumes --remove-orphans
#         docker compose -f /bot_overlord/docker-compose.yml up -d --build
#         ;;
#     "pull_updates")
#         retrieve_tokens
#         git -C /bot_overlord pull
#         ;;
#     "logs") # "logs" show docker logs
#         docker compose -f /bot_overlord/docker-compose.yml logs -f
#         ;;
#     "shell") # "shell" shell into container
#         docker compose -f /bot_overlord/docker-compose.yml exec <service_name> bash
#         ;;
#     "help")
#         echo "Usage: ./helper.sh [command]"
#         echo ""
#         echo "Commands:"
#         echo "  run               Start the bot normally"
#         echo "  run_and_update    Start the bot and update from Git"
#         echo "  run_clean_slate   Start the bot on a clean slate"
#         echo "  pull_updates      Pull updates from Git"
#         echo "  logs              Show the bot logs"
#         echo "  shell             Shell into the bot container"
#         echo "  help              Show this help message"
#         ;;
#     "alias") #add helper alias to bascrc
#         echo "alias helper='bash /bot_overlord/helper.sh'" >> ~/.bashrc
#         ;;
#     *)
#         echo "Invalid command. Use './helper.sh help' to see available commands."
#         ;;
# esac


# # optional later on stuff
#     # copy_to_remote shortcut use on local system to copy helper.sh to remote system

#     # "alias" add "helper" alias to bashrc

#     # "first_run" perform checks, make sure dir for bind mount exists, check folder/file perms, pull tokens, etc




