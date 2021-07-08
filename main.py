#!/usr/bin/env python3
import base64
import re
import os
import sys
from datetime import datetime, timedelta, timezone
from calendar import monthrange
from github import Github, GithubException

START_COMMENT = "<!-- Start of Time Progress Bar -->"
END_COMMENT = "<!-- End of Time Progress Bar -->"
reg = f"{START_COMMENT}[\\s\\S]+{END_COMMENT}"
GRAPH_LENGTH = 30

BLOCKS = os.getenv("INPUT_BLOCKS")
REPOSITORY = os.getenv("INPUT_REPOSITORY")
GH_TOKEN = os.getenv("INPUT_GT_TOKEN")
COMMIT_MESSAGE = os.getenv("INPUT_COMMIT_MESSAGE")
TIME_ZONE = os.getenv("INPUT_TIME_ZONE")

now = datetime.now()
this_year = now.year
this_month = now.month
this_day = now.day
this_date = now.weekday()


def gen_progress_bar(progress: float) -> str:
    """
    Generate progress bar
    """
    passed_progress_bar_index = int(progress * GRAPH_LENGTH)
    bar = BLOCKS[3] * passed_progress_bar_index
    passed_remainder_progress_bar = \
        BLOCKS[2] if (progress * GRAPH_LENGTH - passed_progress_bar_index) >= 0.5 else BLOCKS[1]
    bar += passed_remainder_progress_bar
    bar += BLOCKS[0] * (GRAPH_LENGTH - len(bar))
    return bar


def decode_readme(data: str) -> str:
    """
    Decode the contents of old readme
    """
    decode_bytes = base64.b64decode(data)
    return str(decode_bytes, 'utf-8')


def get_graph() -> str:
    """
    Get final graph.
    """
    # Year Progress
    start_time_of_this_year = datetime(this_year, 1, 1, 0, 0, 0).timestamp()
    end_time_of_this_year = datetime(this_year, 12, 31, 23, 59, 59).timestamp()
    progress_of_this_year = \
        (datetime.now().timestamp() - start_time_of_this_year) / (end_time_of_this_year - start_time_of_this_year)
    progress_bar_of_this_year = gen_progress_bar(progress_of_this_year)

    # Month Progress
    last_day_of_this_month = monthrange(this_year, this_month)[1]
    start_time_of_this_month = datetime(this_year, this_month, 1, 0, 0, 0).timestamp()
    end_time_of_this_month = datetime(this_year, this_month, last_day_of_this_month, 23, 59, 59).timestamp()
    progress_of_this_month = \
        (datetime.now().timestamp() - start_time_of_this_month) / (end_time_of_this_month - start_time_of_this_month)
    progress_bar_of_this_month = gen_progress_bar(progress_of_this_month)

    # Week Progress
    start_time_of_this_week = (
                datetime(this_year, this_month, this_day, 0, 0, 0) - timedelta(days=this_date)).timestamp()
    end_time_of_this_week = \
        (datetime(this_year, this_month, this_day, 23, 59, 59) + timedelta(days=6 - this_date)).timestamp()
    progress_of_this_week = \
        (datetime.now().timestamp() - start_time_of_this_week) / (end_time_of_this_week - start_time_of_this_week)
    progress_bar_of_this_week = gen_progress_bar(progress_of_this_week)

    # Update time
    tz = int(TIME_ZONE)
    update_time = datetime.utcnow() \
        .replace(tzinfo=timezone.utc) \
        .astimezone(timezone(timedelta(hours=tz))) \
        .strftime('%Y-%m-%d %H:%M:%S %p')

    # content
    return f"\
    ``` text\n\
    Year  progress {{ {progress_bar_of_this_year}  }} {format(progress_of_this_year * 100, '0>5.2f')} %\n\
    Month progress {{ {progress_bar_of_this_month}  }} {format(progress_of_this_month * 100, '0>5.2f')} %\n\
    Week  progress {{ {progress_bar_of_this_week}  }} {format(progress_of_this_week * 100, '0>5.2f')} %\n\
    ```\n\
    \n\
    ⏰ *Updated at {update_time} UTC{TIME_ZONE}*\n\
    "


def gen_new_readme(graph: str, readme: str) -> str:
    """
    Generate a new README.md
    """
    return re.sub(reg, f"{START_COMMENT}\n{graph}\n{END_COMMENT}", readme)


if __name__ == '__main__':
    g = Github(GH_TOKEN)
    try:
        repository = g.get_repo(REPOSITORY)
    except GithubException:
        print("Authentication Error. Try saving a GitHub Token in your Repo Secrets or Use the GitHub Actions Token, \
              which is automatically used by the action.")
        sys.exit(1)
    if len(BLOCKS) < 1:
        print("Invalid blocks string. Please provide a string with 2 or more characters. Eg. '░▒▓█'")
        sys.exit(1)
    undecoded_contents = repository.get_readme()
    contents = decode_readme(undecoded_contents.content)
    new_graph = get_graph()
    new_readme = gen_new_readme(new_graph, contents)
    if new_readme != contents:
        repository.update_file(path=undecoded_contents.path, message=COMMIT_MESSAGE,
                               content=new_readme, sha=undecoded_contents.sha)
