# CollabHub

A platform where small and medium businesses find bloggers for advertising.
Businesses create campaigns, bloggers apply, both sides agree on a contract,
and the blogger publishes the content.

Django midterm project, KBTU.

## Team

- Danelya Mubarakova — team lead, project setup, deliverables
- Dastan — users
- Birzhan — campaigns
- Azat — contracts
- Aidana — collaborations

## How to run

    git clone https://github.com/mubarakkkova/collabhub.git
    cd collabhub
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    python manage.py runserver