# azure-face-api-identifier-kube  
## 概要  
1枚の画像を Azure Face API(Detect) にかけ、返り値として、画像に映っているすべての人物の顔の位置座標(X軸/Y軸)、性別・年齢等の情報を取得します。  
Azure Face API の仕様により、顔の位置座標を形成する長方形の面積が最も広い顔が先頭に来ます。  
この仕様を利用して、その先頭の顔の FaceID、性別・年齢 等の 情報 を取得・保持します。  
最後に、取得・保持されたFaceIDを、SQLに保存された登録済みの顔IDと照らし合わせ、SQLに存在すれば登録済み既存ユーザーと判定し、存在しなければ新規ユーザーと判定します。  
なお、本マイクロサービスは、顔認証のデータ解析のために、ログデータを出力します。

参考：Azure Face API の Person Group は、Azure Face API ユーザ のインスタンス毎に独立した顔情報の維持管理の単位です。  
参考：1枚の画像に対して複数の顔が存在する場合は、1番確証度が大きい顔に対して判定を行います。  

## 前提条件  
Azure Face API サービス に アクセスキー、エンドポイント、Person Group を登録します。  
登録されたエンドポイント、アクセスキー、Person Group を、本リポジトリ内の face-api-config.json に記載してください。  

## Azure Face API(Detect) の テスト実行  
Azure Face API(Detect) の テスト実行 をするときは、sample/test_01.jpgに任意の顔画像を配置してください。  
Azure FAce API 登録されているエンドポイントを、事前に学習させます。下記の手順で学習させることができます。  
```
# shellディレクトリ内のrecreate-group.shを実行します。シェル内のENDPOINT, SUBSCRIPTION_KEY, PERSON_GROUP_IDは使用するFaceAPIのエンドポイントに応じて書き換えて下さい。
$ bash recreate-group.sh
# 上記のコマンド実行するとPerson_idが出力されるので、train.shの3行目のPERSON_IDの値を置換しシェルを実行して下さい。
$ bash train.sh
```
* SQLにface_id_azure (TEXT), guest_id (INT) カラムを持つguestテーブルを作成しておきます。  
* `shell/setup-env.sh`　は、face-api-config.jsonと.envを作成するためのシェルスクリプトです。    

## Requirements  
```
azure-cognitiveservices-vision-face==0.4.1
```
## I/O
#### Input
入力データのJSONフォーマットは、inputs/sample.json にある通り、次の様式です。
```
{
    "guest_key": "xxxxxxxxxxxxx",
    "image_path": "/var/lib/aion/Data/direct-next-service_1/1634173065679.jpg"
}
```
1. 顧客ID(guest_key)  
(エッジ)アプリケーションの顧客ID???  
2. 顔画像のパス(image_path)  
入力顔画像のパス  

#### Output1
出力データのJSONフォーマットは、outputs/sample.json にある通り、次の様式です。
```
{
    "result": true,
    "filepath": "/var/lib/aion/Data/direct-next-service_1/634173065679.jpg",
    "guest_id": 1,
    "face_id_azure": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "attributes": {
        "gender": "male",
        "age": "37.0"
    }
}
```
#### Output2
ログデータ(顔認証ログデータ解析用)のJSONフォーマットは、outputs/sample.json にある通り、次の様式です。
```
{
    "imagePath": "/var/lib/aion/Data/direct-next-service_1/1634173065679.jpg",
    "faceId": "00000000-0000-0000-0000-000000000000",
    "responseData": {
        "candidates": []
    }
}
```

## Getting Started
1. 下記コマンドでDockerイメージを作成する。  
```
make docker-build
```
2. aion-service-definitions/services.ymlに設定を記載し、AionCore経由でKubernetesコンテナを起動する。  
services.ymlへの記載例  
multiple: noとして起動する。  
```
azure-face-api-identifier-kube:
  multiple: no
  env:
    MYSQL_USER: XXXXXXXX
    MYSQL_HOST: mysql
    MYSQL_PASSWORD: xxxxxxxxx
    MYSQL_DB: database
    KANBAN_ADDR: aion-statuskanban:10000
    RABBITMQ_URL: amqp://username:password@rabbitmq:5672/virtualhost
    QUEUE_FROM: queue_from
    QUEUE_TO: queue_to
    QUEUE_TO_FOR_LOG: queue_to_for_log
```
## Flowchart
![フローチャート図](doc/face-recognition-flowchart.png)