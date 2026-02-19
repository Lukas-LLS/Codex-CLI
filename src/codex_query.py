# -*- coding: utf-8 -*-

import configparser
import os
import re
import sys
from pathlib import Path

import openai
import psutil
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from commands import get_command_result
from prompt_file import PromptFile

MULTI_TURN = "off"
SHELL = ""

CLIENT_DATA = {}
MODEL = ''
TEMPERATURE = 0
MAX_TOKENS = 300

DEBUG_MODE = False

# api keys located in the same directory as this file
API_KEYS_LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'openaiapirc')

PROMPT_CONTEXT = Path(__file__).with_name('current_context.txt')


# Read the secret_key from the ini file ~/.config/openaiapirc
# The format is:
# [openai]
# organization=<organization-id>
# secret_key=<your secret key>
# model=<model-name>
def create_template_ini_file():
    """
    If the ini file does not exist, create it and add secret_key
    """
    if not os.path.isfile(API_KEYS_LOCATION):
        print('# Please create a file at {} and add your secret key'.format(API_KEYS_LOCATION))
        print('# The format is:\n')
        print('# [openai]')
        print('# organization_id=<organization-id>')
        print('# secret_key=<your secret key>\n')
        print('# model=<model-id>')
        sys.exit(1)


def initialize():
    """
    Initialize openAI and shell mode
    """
    global MODEL
    global CLIENT_DATA

    # Check if the file at API_KEYS_LOCATION exists
    create_template_ini_file()
    config_parser = configparser.ConfigParser()
    config_parser.read(API_KEYS_LOCATION)

    api_key = config_parser['openai']['secret_key'].strip('"').strip("'")
    organization = config_parser['openai']['organization_id'].strip('"').strip("'")

    CLIENT_DATA = {
        'api_key': api_key,
        'organization': organization
    }
    MODEL = config_parser['openai']['model'].strip('"').strip("'")

    prompt_config = {
        'model': MODEL,
        'temperature': TEMPERATURE,
        'max_tokens': MAX_TOKENS,
        'shell': SHELL,
        'multi_turn': MULTI_TURN,
        'token_count': 0
    }

    return PromptFile(PROMPT_CONTEXT.name, prompt_config)


def get_query(prompt_file_config):
    """
    Uses the stdin to get user input
    the input is either treated as a command or as a Codex query

    Returns: command result or context + input from stdin
    """

    # get input from terminal or stdin
    if DEBUG_MODE:
        entry = input("prompt: ") + '\n'
    else:
        entry = sys.stdin.read()
    # first, we check if the input is a command
    command_result, prompt_file_config = get_command_result(entry, prompt_file_config)

    # if input is not a command, then query Codex; otherwise exit command has been run successfully
    if command_result == "":
        return entry, prompt_file_config
    else:
        return sys.exit(0)


def detect_shell():
    global SHELL
    global PROMPT_CONTEXT

    parent_process_name = psutil.Process(os.getppid()).name()
    powershell_mode = bool(re.fullmatch('pwsh|pwsh.exe|powershell.exe', parent_process_name))
    bash_mode = bool(re.fullmatch('bash|bash.exe', parent_process_name))
    zsh_mode = bool(re.fullmatch('zsh|zsh.exe', parent_process_name))

    SHELL = "powershell" if powershell_mode else "bash" if bash_mode else "zsh" if zsh_mode else "unknown"

    shell_prompt_file = Path(os.path.join(os.path.dirname(__file__), "..", "contexts", "{}-context.txt".format(SHELL)))

    if shell_prompt_file.is_file():
        PROMPT_CONTEXT = shell_prompt_file


if __name__ == '__main__':
    detect_shell()
    prompt_file = initialize()
    client = OpenAI(
        api_key=CLIENT_DATA['api_key'],
        organization=CLIENT_DATA['organization']
    )

    try:
        user_query, prompt_file = get_query(prompt_file)

        config = prompt_file.config if prompt_file else {
            'model': MODEL,
            'temperature': TEMPERATURE,
            'max_tokens': MAX_TOKENS,
            'shell': SHELL,
            'multi_turn': MULTI_TURN,
            'token_count': 0
        }

        codex_query = prompt_file.read_prompt_file(user_query) + user_query

        # get the response from openAI

        system_message_content = (
                ('You are a shell code assistant, complete the textual query of the user with a valid shell command. '
                 'The specific shell type is ') + config['shell'] +
                '. If the user wants a textual reply, your reply should be prefixed with a comment symbol based on the '
                'shell type. You must not use code blocks to respond to the user, write commands directly.')

        response = client.chat.completions.create(
            model=config['model'],
            user="codex-cli",
            messages=[
                ChatCompletionSystemMessageParam(role='system', content=system_message_content),
                ChatCompletionUserMessageParam(role='user', content=codex_query),
            ],
            temperature=config['temperature'],
            max_completion_tokens=config['max_tokens'],
            n=1,
        )

        completion_all = response.choices[0].message.content

        print(completion_all)

        # append output to prompt context file
        if config['multi_turn'] == "on":
            if completion_all != "" or len(completion_all) > 0:
                prompt_file.add_input_output_pair(user_query, completion_all)

    except FileNotFoundError:
        print('\n\n# Codex CLI error: Prompt file not found, try again')
    except openai.RateLimitError:
        print('\n\n# Codex CLI error: Rate limit exceeded, try later')
    except openai.APIConnectionError:
        print('\n\n# Codex CLI error: API connection error, are you connected to the internet?')
    except openai.BadRequestError as e:
        print('\n\n# Codex CLI error: Invalid request - ' + str(e))
    except Exception as e:
        print('\n\n# Codex CLI error: Unexpected exception - ' + str(e))
