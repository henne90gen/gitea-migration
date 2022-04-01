import requests
import os
from dataclasses import dataclass


@dataclass
class UserData:
    name: str
    api_token: str


def migrate_repo(gitea_url: str, gitea_user: UserData, user: UserData, service: str, repo_name: str):
    clone_addr = f"https://{service}.com/{user.name}/{repo_name}.git"

    result = requests.post(f"{gitea_url}/api/v1/repos/migrate", headers={"Authorization": f"token {gitea_user.api_token}"}, data={
        "auth_token": user.api_token,
        "clone_addr": clone_addr,
        "description": "",
        "issues": False,
        "labels": False,
        "lfs": False,
        "milestones": False,
        "mirror": True,
        "mirror_interval": "8h",
        "private": True,
        "pull_requests": False,
        "releases": False,
        "repo_name": repo_name,
        "repo_owner": gitea_user.name,
        "service": service,
        "wiki": False
    })

    if result.status_code == 409 and result.json()["message"] == "The repository with the same name already exists.":
        print(f"Already migrated {repo_name}")
        return

    if result.status_code != 200 and result.status_code != 201:
        print(f"Failed to mirror repository {repo_name}")
        print(result.status_code)
        print(result.json())
        exit(1)

    print(f"Migrated {repo_name}")


def migrate_github(gitea_url: str, gitea_user: UserData, github_user: UserData):
    print()
    print("GitHub:")
    url = f"https://api.github.com/search/repositories?q=user:{github_user.name}%20fork:true"
    result = requests.get(url, params={"per_page": 100}, headers={
                          "Authorization": f"token {github_user.api_token}", "Accept": "application/vnd.github.v3+json"})

    json = result.json()
    if result.status_code != 200:
        print(json)
        return

    repos = json["items"]
    for repo in repos:
        repo_name = repo["name"]
        migrate_repo(gitea_url, gitea_user, github_user, "github", repo_name)

    return len(repos)


def migrate_gitlab(gitea_url: str, gitea_user: UserData, gitlab_user: UserData):
    print()
    print("GitLab:")
    result = requests.get("https://gitlab.com/api/v4/projects", params={"simple": True, "owned": True},
                          headers={"Authorization": f"Bearer {gitlab_user.api_token}"})
    if result.status_code != 200:
        print("Failed to fetch repository list for GitLab")
        return

    count = 0
    repos = result.json()
    for repo in repos:
        if repo["namespace"]["path"] != gitlab_user.name:
            print(f"Skipping {repo['name_with_namespace']}")
            continue
        repo_name = repo["path"]
        migrate_repo(gitea_url, gitea_user, gitlab_user, "gitlab", repo_name)
        count += 1
    return count


def main():
    gitea_url = "<Gitea Url>"
    gitea_user = UserData(
        "<Gitea User Name>", "<Gitea API Token>")
    github_user = UserData(
        "<GitHub User Name>", "<GitHub API Token>")
    gitlab_user = UserData("<GitLab User Name>", "<GitLab API Token>")

    count = 0
    count += migrate_github(gitea_url, gitea_user, github_user)
    count += migrate_gitlab(gitea_url, gitea_user, gitlab_user)

    print()
    print(f"Migrated {count} repositories")


if __name__ == "__main__":
    main()
