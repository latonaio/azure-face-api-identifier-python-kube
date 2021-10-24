#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) Latona. All rights reserved.
import asyncio
import json
import os
import sys
import logging
import MySQLdb

# Azure Face API用モジュール
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

# redis用モジュール
import redis

# rabbitMQ用モジュール
from rabbitmq_client import RabbitmqClient

# JSONロギング用モジュール
from custom_logger import init_logger


BASE_PATH = os.path.join(os.path.dirname(__file__), )
SERVICE_NAME = 'azure-face-api-identifier-kube'
DEFAULT_REDIS_HOST = 'redis-cluster'
PERSON_GROUP_ID = ''
logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(host=DEFAULT_REDIS_HOST, port=6379)
    def hmset(self, key, value):
        self.client.hmset(key, value)

class FaceRecognition():
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'face-api-config.json'), 'r') as f:
            settings = json.load(f)

        # set PERSON_GROUP_ID from json
        global PERSON_GROUP_ID
        PERSON_GROUP_ID = settings.get('PERSON_GROUP_ID')

        # Create an authenticated FaceClient.
        self.face_client = FaceClient(
            settings.get('API_ENDPOINT'),
            CognitiveServicesCredentials(settings.get('API_ACCESS_KEY'))
        )

    def detectFacesFromImage(self, faceImage: str):
        params = ['gender', 'age']
        with open(faceImage, 'r+b') as image:
            # detect faces
            faces = self.face_client.face.detect_with_stream(image, return_face_attributes=params)
        return faces

    def identityFromRegisterdFace(self, face):
        face_id = [face.face_id]
        person_list = []
        persons = self.face_client.face.identify(face_id, PERSON_GROUP_ID, max_num_of_candidates_returned=5)
        for person in persons:
            if person.candidates:
                for candidate in person.candidates:
                # candidate = person.candidates[0]  # itiban match takai
                    if person.face_id == face.face_id:
                        person_list.append({
                            'additional_properties': candidate.additional_properties,
                            'person_id': candidate.person_id,
                            'confidence': candidate.confidence,
                        })

        return person_list


class MySQLAccess:
    def __init__(self):
        self.connection = MySQLdb.connect(
            host=os.environ['MYSQL_HOST'],
            user=os.environ['MYSQL_USER'],
            passwd=os.environ['MYSQL_PASSWORD'],
            db=os.environ['MYSQL_DB'],
            charset='utf8')
        self.cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)

    def check_guest_database(self, person_id: str):
        sql = '''
            SELECT
                guest_id
            FROM guest
            WHERE face_id_azure = "%s"
        ''' % (person_id)
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        if res:
            return res.get('guest_id')
        else:
            return None


async def main():
    init_logger()
    # RabbitMQ接続情報
    rabbitmq_url = os.environ['RABBITMQ_URL']
    # キューの読み込み元
    queue_from = os.environ['QUEUE_FROM']
    # キューの書き込み先
    queue_to_for_log = os.environ['QUEUE_TO_FOR_LOG']

    try:
        mq_client = await RabbitmqClient.create(rabbitmq_url, {queue_from}, {queue_to_for_log})
    except Exception as e:
        logger.error({
            'message': 'failed to connect rabbitmq!',
            'error': str(e),
            'queue_from': queue_from,
            'queue_to_for_log': queue_to_for_log,
        })
        # 本来 sys.exit を使うべきだが、効かないので
        os._exit(1)

    logger.info('create mq client')

    async for message in mq_client.iterator():
        # async with内でエラーが発生した場合、RabbitMQのデッドレターにエラーメッセージを送る。
        # with内のtry内部でエラーが発生した場合、exceptがエラーを捕まえるので、withはエラーを検知しない。
        async with message.process():
            logger.info({
                'message': 'message received',
                'params': message.data,
            })

            # キューからVR画像パスを取得
            vr_image = message.data.get('image_path')
            redis_key = message.data.get('guest_key')
            # FaceAPIに接続
            fr = FaceRecognition()
            # Face: どの人物に該当するかを判定する
            try:
                faces = fr.detectFacesFromImage(vr_image)
                if not faces:
                    raise Exception('face is not detected')
                person_list = fr.identityFromRegisterdFace(faces[0])
                if len(person_list) == 0:
                    person = None
                else:
                    person = person_list[0] # itiban match takai
                msa = MySQLAccess()
                if person is not None:
                    logger.info('person id: {}'.format(str(person)))
                    res = msa.check_guest_database(str(person.get('person_id')))
                if person is not None and res and person["confidence"]>0.60:
                    logger.info('detect existing face (guestid: {})'.format(str(res)))
                    data = {
                        'connection_key': 'response',
                        'result': True,
                        'redis_key': redis_key,
                        'filepath': vr_image,
                        'person': person,
                        'guest_id': res,
                        'status': 'existing'
                    }
                    logger.debug({
                        'message': 'send message',
                        'params': data
                    })
                else:
                    data = {
                        'connection_key': 'response',
                        'result': True,
                        'redis_key': redis_key,
                        'filepath': vr_image,
                        'status': 'new',
                        'age': faces[0].face_attributes.age,
                        'gender': str(faces[0].face_attributes.gender).lstrip('Gender.'),
                    }
                    logger.info({
                        'message': 'send message: detect new face',
                        'params': data,
                    })

                # 顔認証ログ：ログサービス転送用
                payload_for_log = {
                    "imagePath": vr_image,
                    "faceId": faces[0].face_id,
                    "responseData": {
                        "candidates": person_list,
                    }
                }
                logger.debug({
                    'message': 'send message for log',
                    'params': payload_for_log
                })

                await mq_client.send(queue_to_for_log, payload_for_log)
                logger.info('sent message to %s', queue_to_for_log)

                await insert_data_to_redis(data)

            except Exception as e:
                logger.error({
                    'message': 'error',
                    'error': str(e),
                })
                data = {
                    'connection_key': 'response',
                    'result': False,
                    'redis_key': redis_key,
                    'microservice': SERVICE_NAME,
                }
                logger.debug({
                    'message': 'send message',
                    'params': data,
                })

                await insert_data_to_redis(data)


async def insert_data_to_redis(data):
            try:
                redis_key = int(data.get('redis_key'))
                customer = data.get('status')
                prior_res = data.get('result')

                if prior_res and customer == 'existing':
                    data = {
                        'status': 'success',
                        'customer': customer,
                        'guest_id': int(data.get('guest_id')),
                    }
                    logger.debug({
                        'message': 'redis data',
                        'params': data
                    })
                elif prior_res and customer == 'new':
                    data = {
                        'status': 'success',
                        'customer': customer,
                        'age_by_face': int(data.get('age')),
                        'gender_by_face': data.get('gender'),
                        'image_path': data.get('filepath'),
                    }
                    logger.debug({
                        'message': 'redis data',
                        'params': data
                    })
                else:
                    data = {
                        'status': 'failed',
                        'customer': '',
                        'guest_id': '',
                        'failed_ms': data.get('microservice')
                    }
                    logger.debug({
                        'message': 'redis data',
                        'params': data
                    })

                rc = RedisClient()
                rc.hmset(redis_key, data)
                logger.info('insert redis')

            except Exception as e:
                logger.error({
                    'message': 'error',
                    'error': str(e),
                })

if __name__ == '__main__':
    asyncio.run(main())
