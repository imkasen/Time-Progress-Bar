"""
Entry file
"""
#!/usr/bin/env python3
import base64
import os
import re
import sys
from calendar import monthrange
from datetime import datetime, timedelta, timezone

from github import Github, GithubException

START_COMMENT: str = "<!-- Start of Time Progress Bar -->"
END_COMMENT: str = "<!-- End of Time Progress Bar -->"
REG: str = f"{START_COMMENT}[\\s\\S]+{END_COMMENT}"
GRAPH_LENGTH: int = 30

BLOCKS: str = os.getenv("INPUT_BLOCKS")
REPOSITORY: str = os.getenv("INPUT_REPOSITORY")
GH_TOKEN: str = os.getenv("INPUT_GH_TOKEN")
COMMIT_MESSAGE: str = os.getenv("INPUT_COMMIT_MESSAGE")
TIME_ZONE: str = os.getenv("INPUT_TIME_ZONE")

if TIME_ZONE and int(TIME_ZONE) >= 0 and not TIME_ZONE.startswith("+"):
    TIME_ZONE = "+" + TIME_ZONE
if TIME_ZONE and (int(TIME_ZONE) > 14 or int(TIME_ZONE) < -12):
    sys.exit("UTC timezone should be in the range of '-12' to '14'!")


def gen_progress_bar(progress: float) -> str:
    """
    Generate progress bar
    """
    passed_progress_bar_index: int = int(progress * GRAPH_LENGTH)
    progress_bar: str = BLOCKS[-1] * passed_progress_bar_index
    proportion: float = 1 / (len(BLOCKS) - 2)
    index: int = int((progress * GRAPH_LENGTH - passed_progress_bar_index) / proportion) + 1
    passed_remainder_progress_bar: str = BLOCKS[index]
    progress_bar += passed_remainder_progress_bar
    progress_bar += BLOCKS[0] * (GRAPH_LENGTH - len(progress_bar))
    return progress_bar


def decode_readme(data: str) -> str:
    """
    Decode the contents of old readme
    """
    decode_bytes: bytes = base64.b64decode(data)
    return str(decode_bytes, "utf-8")


def gen_new_readme(graph: str, readme: str) -> str:
    """
    Generate a new README.md
    """
    return re.sub(REG, f"{START_COMMENT}\n{graph}\n{END_COMMENT}", readme)


def get_graph(tz: timezone, this_year: int, this_month: int, this_day: int, this_date: int) -> str:
    """
    Get final graph.
    """
    # Update time
    update_time: str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %p")

    # Year Progress
    start_time_of_this_year: float = datetime(this_year, 1, 1, 0, 0, 0, tzinfo=tz).timestamp()
    end_time_of_this_year: float = datetime(this_year, 12, 31, 23, 59, 59, tzinfo=tz).timestamp()
    progress_of_this_year: float = (datetime.now(tz).timestamp() - start_time_of_this_year) / (
        end_time_of_this_year - start_time_of_this_year
    )
    progress_bar_of_this_year: str = gen_progress_bar(progress_of_this_year)

    # Month Progress
    last_day_of_this_month: int = monthrange(this_year, this_month)[1]
    start_time_of_this_month: float = datetime(this_year, this_month, 1, 0, 0, 0, tzinfo=tz).timestamp()
    end_time_of_this_month: float = datetime(
        this_year, this_month, last_day_of_this_month, 23, 59, 59, tzinfo=tz
    ).timestamp()
    progress_of_this_month: float = (datetime.now(tz).timestamp() - start_time_of_this_month) / (
        end_time_of_this_month - start_time_of_this_month
    )
    progress_bar_of_this_month: str = gen_progress_bar(progress_of_this_month)

    # Week Progress
    start_time_of_this_week: float = (
        datetime(this_year, this_month, this_day, 0, 0, 0, tzinfo=tz) - timedelta(days=this_date)
    ).timestamp()
    end_time_of_this_week: float = (
        datetime(this_year, this_month, this_day, 23, 59, 59, tzinfo=tz) + timedelta(days=6 - this_date)
    ).timestamp()
    progress_of_this_week: float = (datetime.now(tz).timestamp() - start_time_of_this_week) / (
        end_time_of_this_week - start_time_of_this_week
    )
    progress_bar_of_this_week: str = gen_progress_bar(progress_of_this_week)

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


if __name__ == "__main__":
    g = Github(GH_TOKEN)
    try:
        repository = g.get_repo(REPOSITORY)
    except GithubException:
        sys.exit(
            "Authentication Error. \
            Try saving a GitHub Token in your Repo Secrets or Use the GitHub Actions Token, \
            which is automatically used by the action."
        )
    if len(BLOCKS) < 1:
        sys.exit("Invalid blocks string. Please provide a string with 2 or more characters. Eg. '░▒▓█'")

    TZ: timezone = timezone(timedelta(hours=int(TIME_ZONE)))
    NOW_TIME: datetime = datetime.now(TZ)
    THIS_YEAR: int = NOW_TIME.year
    THIS_MONTH: int = NOW_TIME.month
    THIS_DAY: int = NOW_TIME.day
    THIS_DATE: int = NOW_TIME.weekday()

    undecoded_contents = repository.get_readme()
    contents: str = decode_readme(undecoded_contents.content)
    new_graph: str = get_graph(TZ, THIS_YEAR, THIS_MONTH, THIS_DAY, THIS_DATE)
    new_readme: str = gen_new_readme(new_graph, contents)
    if new_readme != contents:
        repository.update_file(
            path=undecoded_contents.path,
            message=COMMIT_MESSAGE,
            content=new_readme,
            sha=undecoded_contents.sha,
        )
