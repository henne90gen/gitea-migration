# Gitea Migration

Script to mirror all GitHub and GitLab repositories of a user to Gitea.

Create a `config.json` like this:

```json
{
    "gitea_url": "<url of gitea instance>",
    "gitea_user": {
        "name": "<gitea username>",
        "api_token": "<gitea api token>"
    },
    "github_user": {
        "name": "<github username>",
        "api_token": "<github api token>"
    },
    "gitlab_user": {
        "name": "<gitlab username>",
        "api_token": "<gitlab api token>"
    }
}
```

Optionally create a virtual environment with `virtualenv` and install the dependencies.
Then run the script.

```shell
virtualenv venv && . venv/bin/activate # optional
pip install -r requirements.txt
python main.py
```
