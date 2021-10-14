#!/usr/bin/env python3
# coding: utf-8

import json
import os

# Azure Face API用モジュール
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

from dotenv import load_dotenv
load_dotenv()

PERSON_GROUP_ID = os.getenv('PERSON_GROUP_ID')
FACE_API_CONFIG_PATH = "../face-api-config.json"
TEST_IMAGE_PATH = "../sample/test_04.jpg"


class FaceRecognition():
    def __init__(self):
        settings = json.load(
            open(os.path.join(os.path.dirname(__file__), FACE_API_CONFIG_PATH), "r")
        )
        # Create an authenticated FaceClient.
        self.face_client = FaceClient(
            settings.get('API_ENDPOINT'),
            CognitiveServicesCredentials(settings.get('API_ACCESS_KEY'))
        )

    def detect_faces_from_image(self, face_image: str):
        params = ['gender', 'age']
        image = open(face_image, 'r+b')
        # Detect faces
        faces = self.face_client.face.detect_with_stream(image, return_face_attributes=params)
        return faces

    def identityFromRegisterdFace(self, face):
        face_id = [face.face_id]
        person_list = []
        persons = self.face_client.face.identify(face_id, PERSON_GROUP_ID)
        for person in persons:
            if person.candidates:
                candidate = person.candidates[0] # itiban match takai
                if person.face_id == face.face_id:
                    person = {
                        'person_id': candidate.person_id,
                        'confidence': candidate.confidence,
                    }
                    return person
            else:
                return None


def main():
    try:
        fr = FaceRecognition()
        faces = fr.detect_faces_from_image(TEST_IMAGE_PATH)
        if not faces:
            raise Exception("face is not detected")
        person = fr.identityFromRegisterdFace(faces[0])
        print(person)
        if person is not None:
            print("person id: {}".format(str(person)))
            # res = msa.check_guest_database(str(person.get('person_id')))
    except Exception as e:
        print(str(e))


main()
