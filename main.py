import requests
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserData:
    name: str
    api_token: str
    force_migration: bool = False


@dataclass
class Config:
    gitea_url: str
    gitea_user: UserData
    github_user: UserData
    gitlab_user: UserData


def migrate_repo(gitea_url: str, gitea_user: UserData, user: UserData, service: str, repo_name: str):
    if repo_name in ["lecture_scripts"]:
        # NOTE: these repositories take too long to sync
        print("Skipping", repo_name)
        return
    
    headers = {"Authorization": f"token {gitea_user.api_token}"}
    if user.force_migration:
        result = requests.delete(f"{gitea_url}/api/v1/repos/{gitea_user.name}/{repo_name}", headers=headers)

        if result.status_code != 204 and result.status_code != 404:
            print(f"Failed to delete repository {repo_name} before migrating it again.")
            print(result.status_code)
            print(result.content.decode("utf-8"))
            exit(1)

    clone_addr = f"https://{service}.com/{user.name}/{repo_name}.git"
    result = requests.post(f"{gitea_url}/api/v1/repos/migrate", headers=headers, data={
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
        print(result.content.decode("utf-8"))
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


def load_config() -> Optional[Config]:
    with open("config.json") as f:
        json_dict = json.load(f)

    if "gitea_url" not in json_dict:
        print("Missing 'gitea_url' in config.json")
        return None

    def load_user_data(user_field_name: str) -> Optional[UserData]:
        if user_field_name not in json_dict:
            print(f"Missing '{user_field_name}' in config.json")
            return None

        if "name" not in json_dict[user_field_name]:
            print(f"Missing '{user_field_name}.name' in config.json")
            return None

        if "api_token" not in json_dict[user_field_name]:
            print(f"Missing '{user_field_name}.api_token' in config.json")
            return None

        force_migration = False
        if "force_migration" in json_dict[user_field_name]:
            force_migration = json_dict[user_field_name]["force_migration"]

        return UserData(
            name=json_dict[user_field_name]["name"],
            api_token=json_dict[user_field_name]["api_token"],
            force_migration=force_migration
        )

    gitea_user = load_user_data("gitea_user")
    if gitea_user is None:
        return None

    github_user = load_user_data("github_user")
    if github_user is None:
        return None

    gitlab_user = load_user_data("gitlab_user")
    if gitlab_user is None:
        return None

    return Config(
        gitea_url=json_dict["gitea_url"],
        gitea_user=gitea_user,
        github_user=github_user,
        gitlab_user=gitlab_user
    )


def main():
    config = load_config()
    if config is None:
        exit(1)

    gitea_url = config.gitea_url
    gitea_user = config.gitea_user
    github_user = config.github_user
    gitlab_user = config.gitlab_user

    count = 0
    count += migrate_github(gitea_url, gitea_user, github_user)
    count += migrate_gitlab(gitea_url, gitea_user, gitlab_user)

    print()
    print(f"Migrated {count} repositories")


if __name__ == "__main__":
    main()
