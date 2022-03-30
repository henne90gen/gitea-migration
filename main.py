import requests
import os


def migrate_repo(repo_name: str, gitea_url: str, gitea_api_token: str, gitea_user: str, github_api_token: str, github_user: str):
    clone_addr = f"https://github.com/{github_user}/{repo_name}.git"

    result = requests.post(f"{gitea_url}/api/v1/repos/migrate", headers={"Authorization": f"token {gitea_api_token}"}, data={
        "auth_token": github_api_token,
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
        "repo_owner": gitea_user,
        "service": "github",
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


def main():
    gitea_api_token = "<Gitea API Token>"
    gitea_user = "<Gitea User>"
    gitea_url = "<Gitea Url>"
    github_api_token = "<GitHub API Token"
    github_user = "<GitHub User>"

    url = f"https://api.github.com/search/repositories?q=user:{github_user}%20fork:true"
    result = requests.get(url, params={"per_page": 100}, headers={
                          "Authorization": f"token {github_api_token}", "Accept": "application/vnd.github.v3+json"})

    json = result.json()
    if result.status_code != 200:
        print(json)
        return

    repos = json["items"]
    for repo in repos:
        repo_name = repo["name"]
        migrate_repo(repo_name, gitea_url, gitea_api_token,
                     gitea_user, github_api_token, github_user)


if __name__ == "__main__":
    main()
