# with reference to: https://github.com/GGtoms/youth_study

import time
import os
import logging

import re
import json

import requests


def get_account(logger):
    # The first way to get account: from the environment variables
    access_id = os.getenv("YOUTHSTUDY_OPENID")
    if access_id is not None:
        logger.info("Have obtained account information from the environmental variables.")
        return access_id

    # The second way to get account: from the file
    if os.path.exists("account.txt"):
        logger.info("Read the account information from account.txt.")
        with open("account.txt", "r") as account_file:
            access_id = account_file.read()
        return access_id

    else:  # The third way to get account: input
        logger.info("account.txt not found.")
        logger.info("Please input the following account information:")

        access_id = input("YouthStudy OpenID: ")
        with open("account.txt", "w") as account_file:
            account_file.write(access_id)

        logger.info("account.txt saved.")
        logger.info("Please pay attention to the safety of the file.")
        logger.info("A hyperlink to desktop is recommended.")

        return access_id


def get_access_token(access_id):
    access_url = "https://qcsh.h5yunban.com/youth-learning/cgi-bin/login/we-chat/callback"
    access_param = {"appid": "wxa693f4127cc93fad", "openid": access_id}
    access_page = requests.get(access_url, access_param)

    access_regex = r"\('accessToken', '(.+?)'\)"
    access_text = access_page.text
    access_token = re.findall(access_regex, access_text)[0]
    return access_token


def get_course_json(access_token):
    # get the latest course json
    course_url = "https://qcsh.h5yunban.com/youth-learning/cgi-bin/common-api/course/current?accessToken="
    course_url += access_token
    course_page = requests.get(course_url)

    course_json = course_page.json()
    return course_json


def get_group_json(access_token):
    group_url = "https://qcsh.h5yunban.com/youth-learning/cgi-bin/user-api/course/last-info?accessToken="
    group_url += access_token
    group_page = requests.get(group_url)

    group_json = group_page.json()
    return group_json


def get_study_param(access_token, course_id):
    if os.path.exists("group.json"):
        logger.info("Read the group information from group.json.")
        with open("group.json", "rb") as group_file:
            study_param = json.load(group_file)

    else:
        logger.info("group.json not found.")
        logger.info("Start to read the group information online.")
        group_json = get_group_json(access_token)
        try:
            study_param = {"nid": group_json["result"]["nid"],
                           "cardNo": group_json["result"]["cardNo"],
                           "subOrg": group_json["result"]["subOrg"]}
        except KeyError:
            study_param = {"nid": None, "cardNo": None, "subOrg": None}
            logger.info("Fail to read the group information online.")
            logger.info('')
        else:
            logger.info("Successfully read the group information online.")
            with open("group.json", "w") as group_file:
                group_file.write(json.dumps(study_param, indent = 4))
            logger.info("group.json saved.")
            logger.info('')

    study_param["course"] = course_id
    return study_param


def study(access_token, course_id, logger):
    study_url = "https://qcsh.h5yunban.com/youth-learning/cgi-bin/user-api/course/join?accessToken="
    study_url += access_token
    study_param = get_study_param(access_token, course_id)

    logger.info("Start the course.")
    study_post = requests.post(study_url, json = study_param)

    study_json = study_post.json()
    study_status = study_json["status"]

    if study_status == 200:
        logger.info("Successfully complete the course.")
    else:
        logger.info("Fail to complete the course.")


def download_image(course_uri, image_path):
    image_url = course_uri.rpartition("/")[0] + "/images/end.jpg"
    image_page = requests.get(image_url)

    image_content = image_page.content
    with open(image_path, "wb") as image_file:
        image_file.write(image_content)


if __name__ == "__main__":
    log_dir = "logs/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(level = logging.INFO)
    log_path = "logs/%s.log" % time.strftime("%Y%m%d%H%M", time.localtime())
    log_handler = logging.FileHandler(log_path, mode = "w")
    log_formatter = logging.Formatter("%(asctime)s: %(message)s")
    log_handler.setFormatter(log_formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(log_handler)

    image_dir = "images/"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    image_path = "images/%s.jpg" % time.strftime("%Y%m%d%H%M", time.localtime())

    access_id = get_account(logger = logger)
    access_token = get_access_token(access_id)

    course_json = get_course_json(access_token)
    course_id = course_json["result"]["id"]
    course_uri = course_json["result"]["uri"]

    study(access_token, course_id, logger)
    download_image(course_uri, image_path)
