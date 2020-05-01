import os
import subprocess
import colorama
from colorama import Fore, Style
from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result, print_title
from nornir.plugins.tasks.networking import netmiko_send_config
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.tasks.text import template_file
from pyfiglet import Figlet

nr = InitNornir(config_file="config.yaml")
clear_command = "clear"
os.system(clear_command)
custom_fig = Figlet(font='isometric3')
print(custom_fig.renderText('pyNIR'))

def clean_ospf(task):
    r = task.run(task=netmiko_send_command, name="Identifying Current OSPF", command_string = "show run | s ospf")
    output = r.result
    my_list = []
    num = [int(s) for s in output.split() if s.isdigit()]
    for x in num:
        if x == 0:
            continue
        my_list.append("no router ospf " + str(x))
    my_list = list(dict.fromkeys(my_list))
    for commands in my_list:
        task.run(task=netmiko_send_config, name="Removing Current OSPF", config_commands=commands)

    desired_ospf(task)


def desired_ospf(task):
    data = task.run(task=load_yaml, name="Pulling from Definition Files", file=f'./host_vars/{task.host}.yaml')
    task.host["OSPF"] = data.result["OSPF"]
    r = task.run(task=template_file, name="Building Desired State", template="ospf.j2", path="./templates")
    task.host["config"] = r.result
    output = task.host["config"]
    send = output.splitlines()
    task.run(task=netmiko_send_config, name="Implementing OSPF Desired State", config_commands=send)


current = "pyats learn ospf --testbed-file testbed.yaml --output ospf-current"
os.system(current)
command = subprocess.run(["pyats", "diff", "desired-ospf/", "ospf-current", "--output", "ospfdiff"], stdout=subprocess.PIPE)
stringer = str(command)
if "Diff can be found" in stringer:
    os.system(clear_command)
    print(Fore.CYAN + "#" * 70)
    print(Fore.RED + "ALERT: " + Style.RESET_ALL + "CURRENT OSPF CONFIGURATIONS ARE NOT IN SYNC WITH DESIRED STATE!")
    print(Fore.CYAN + "#" * 70)
    print("\n")
    answer = input(Fore.YELLOW +
            "Would you like to reverse the current OSPF configuration back to its desired state? " + Style.RESET_ALL + "<y/n>: "
)
    if answer == "y":
        def main() -> None:
            clean_up = "rm -r ospfdiff ospf-current"
            os.system(clean_up)
            os.system(clear_command)
            nr = InitNornir(config_file="config.yaml")
            output = nr.run(task=clean_ospf)
            print_title("REVERSING OSPF CONFIGURATION BACK INTO DESIRED STATE")
            print_result(output)

        if __name__ == '__main__':
                main()

else:
    clean_up = "rm -r ospfdiff ospf-current"
    os.system(clean_up)
    os.system(clear_command)
    print("*" * 75)
    print(Fore.GREEN + "Good news! OSPF configurations are matching desired state!" + Style.RESET_ALL)
    print("*" * 75)
