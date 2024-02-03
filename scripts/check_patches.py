import requests

def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        return data['tag_name']
    else:
        return data['message']

# Usage
repo = "ReVanced/revanced-patches"  # replace with your repository
print(get_latest_release(repo))
