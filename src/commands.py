import os
import time


def get_command_result(command_input, prompt_file):
    """
    Checks if the input is a command and if so, executes it
    Currently supported commands:
    - start multi-turn
    - stop multi-turn
    - default context
    - show context <n>
    - view context
    - save context
    - clear context
    - load context <filename>
    - set model <model>
    - set temperature <temperature>
    - set max_tokens <max_tokens>
    - set shell <shell>

    Returns: command result or "" if no command matched
    """
    if prompt_file is None:
        return "", None

    config = prompt_file.config
    # configuration setting commands
    if command_input.__contains__("set"):
        # set temperature <temperature>
        if command_input.__contains__("temperature"):
            command_input = command_input.split()
            if len(command_input) == 4:
                config['temperature'] = float(command_input[3])
                prompt_file.set_config(config)
                print("# Temperature set to " + str(config['temperature']))
                return "config set", prompt_file
            else:
                return "", prompt_file
        # set max_tokens <max_tokens>
        elif command_input.__contains__("max_tokens"):
            command_input = command_input.split()
            if len(command_input) == 4:
                config['max_tokens'] = int(command_input[3])
                prompt_file.set_config(config)
                print("# Max tokens set to " + str(config['max_tokens']))
                return "config set", prompt_file
            else:
                return "", prompt_file
        elif command_input.__contains__("shell"):
            command_input = command_input.split()
            if len(command_input) == 4:
                config['shell'] = command_input[3]
                prompt_file.set_config(config)
                print("# Shell set to " + str(config['shell']))
                return "config set", prompt_file
            else:
                return "", prompt_file
        elif command_input.__contains__("model"):
            command_input = command_input.split()
            if len(command_input) == 4:
                config['model'] = command_input[3]
                prompt_file.set_config(config)
                print("# model set to " + str(config['model']))
                return "config set", prompt_file
            else:
                return "", prompt_file

    if command_input.__contains__("show config"):
        prompt_file.show_config()
        return "config shown", prompt_file

    # multi turn/single turn commands
    if command_input.__contains__("multi-turn"):
        # start context
        if command_input.__contains__("start"):
            if config['multi_turn'] == 'off':
                prompt_file.start_multi_turn()
                return "multi turn mode on", prompt_file

            return "multi turn mode on", prompt_file

        # stop context
        if command_input.__contains__("stop"):
            prompt_file.stop_multi_turn()
            return "multi turn mode off", prompt_file

    # context file commands
    if command_input.__contains__("context"):
        if command_input.__contains__("default"):
            prompt_file.default_context()
            return "stopped context", prompt_file

        # show context <n>
        if command_input.__contains__("show"):
            print('\n')
            with open(prompt_file.file_name, 'r') as f:
                lines = f.readlines()
                lines = lines[6:]  # skip headers

            line_numbers = 0
            if len(command_input.split()) > 3:
                line_numbers = int(command_input.split()[3])

            if line_numbers != 0:
                for line in lines[-line_numbers:]:
                    print('\n# ' + line, end='')
            else:
                print('\n# '.join(lines))
            return "context shown", prompt_file

        # edit context
        if command_input.__contains__("view"):
            # open the prompt file in a text editor
            if config['shell'] != 'powershell':
                os.system('open {}'.format(prompt_file.file_path))
            else:
                os.system('start {}'.format(prompt_file.file_path))
            return "context shown", prompt_file

        # save context <filename>
        if command_input.__contains__("save"):
            # save the current prompt file to a new file
            # if the filename is not specified use the current time (to avoid name conflicts)

            filename = time.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
            if len(command_input.split()) == 4:
                filename = command_input.split()[3]

            prompt_file.save_to(filename)
            return "context saved", prompt_file

        # clear context
        if command_input.__contains__("clear"):
            # temporary saving deleted prompt file
            prompt_file.default_context()
            return "unlearned interaction", prompt_file

        # load context <filename>
        if command_input.__contains__("load"):
            # the input looks like # load context <filename>
            # write everything from the file to the prompt file
            command_input = command_input.split()
            if len(command_input) == 4:
                filename = command_input[3]
                prompt_file.load_context(filename)
                return "context loaded", prompt_file
            print('\n#\tInvalid command format, did you specify which file to load?')
            return "context loaded", prompt_file

    return "", prompt_file
