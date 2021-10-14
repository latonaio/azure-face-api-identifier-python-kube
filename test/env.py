import os
from dotenv import load_dotenv
load_dotenv()


def get_env():
    person_group_id = os.getenv('PERSON_GROUP_ID')
    print(person_group_id)


get_env()

