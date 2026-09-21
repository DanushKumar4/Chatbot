"""Terminal formatting helpers for CLI scripts."""

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def header(text: str) -> str:
    return f"\n{BOLD}{BLUE}{'─' * 50}\n  {text}\n{'─' * 50}{RESET}\n"


def agent_label(name: str) -> str:
    colors = {
        "super_agent": BLUE,
        "loan_agent": GREEN,
        "account_agent": "\033[95m",
        "card_agent": YELLOW,
        "complaint_agent": RED,
    }
    color = colors.get(name, DIM)
    return f"{color}{BOLD}[{name}]{RESET}"


def user_msg(text: str) -> str:
    return f"{GREEN}{BOLD}You:{RESET} {text}"


def bot_msg(agent: str, text: str) -> str:
    return f"{agent_label(agent)} {text}"


def info(text: str) -> str:
    return f"{DIM}{text}{RESET}"


def error(text: str) -> str:
    return f"{RED}{BOLD}Error:{RESET} {RED}{text}{RESET}"


def success(text: str) -> str:
    return f"{GREEN}{BOLD}✓{RESET} {text}"
