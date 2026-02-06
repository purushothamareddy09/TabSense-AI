import tldextract

CATEGORY_RULES = {
    "github.com": "Coding",
    "gitlab.com": "Coding",
    "bitbucket.org": "Coding",

    "stackoverflow.com": "Debugging",
    "serverfault.com": "Debugging",

    "docs.": "Learning",
    "aws.amazon.com": "Cloud / DevOps",
    "kubernetes.io": "Cloud / DevOps",

    "jira": "Work / Planning",
    "confluence": "Work / Docs",

    "youtube.com": "Entertainment",
    "netflix.com": "Entertainment",

    "chat.openai.com": "AI / Research"
}

def classify_activity(url: str, title: str) -> str:
    url = url.lower()
    title = title.lower()

    for key, category in CATEGORY_RULES.items():
        if key in url or key in title:
            return category

    return "Other"