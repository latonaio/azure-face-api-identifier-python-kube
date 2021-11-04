# azure-face-api-identifier-kube  
## 概要  
1枚の画像を Azure Face API(Detect) にかけ、返り値として、画像に映っているすべての人物の顔の、位置座標、性別・年齢、等、の情報を取得します。  
このとき、Azure Face API の仕様により、顔の位置座標を形成する長方形の面積が最も広い顔が先頭に来ます。  
この仕様を利用して、その先頭の顔の FaceID、性別・年齢 等の 情報 を取得・保持します。  
最後に、取得・保持されたFaceIDを、アプリケーションサイドでSQLに保存された登録済みの顔IDと照らし合わせ、SQLに存在すれば登録済み既存ユーザーと判定し、存在しなければ新規ユーザーと判定します。  
なお、本マイクロサービスは、顔認証判定結果のデータ解析のために、ログデータを出力します。  

参考1：Azure Face API の Person Group は、Azure Face API ユーザ のインスタンス毎に独立した顔情報の維持管理の単位です。  

参考2：Azure Face API の仕様により、1つの判定されたFaceIDに対して複数の認証結果の選択肢であるPersonIDが存在する場合、それぞれのPersonIDに対して確証度を付与して出力します。  
このとき、確証度の高い順にPersonIDのデータが並びます。この仕様を利用して、1つのFacdIDに対して、一定の確証度の閾値を設け、その閾値以上の確証度を持つPersonID(大抵の状況ではPersonID=FaceID)とその性別・年齢等の情報を取得・保持します。  

参考3：Azure Face API の仕様では、Azure Face API(Detect)では、FaceID ならびに PersonID は Azure Face API で永続的に管理維持されません。  
Azure face API で永続的にFaceID / PersonID を管理維持する(通常のアプリケーションの要求としてこの行為が必要になります)ためには、別途、Azure Face API(Person Group _ Person - Create / Add Face)を利用する必要があります。この機能の利用については、[azure-face-api-registrator-kube](https://github.com/latonaio/azure-face-api-registrator-kube) を参照してください。

## azure-face-api-identifier-kube を使用したエッジコンピューティングアーキテクチャの一例
![フローチャート図](doc/omotebako_architecture_20211016.drawio.png)


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

## Requirements（Azure Face API の Version 指定)  
azure-face-api の version を指定します。  
本レポジトリの requirements.txt では、下記のように記載されています。  
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
(エッジ)アプリケーションの顧客ID  
2. 顔画像のパス(image_path)  
入力顔画像のパス  

#### Output1-1  
出力データのJSONフォーマットは、outputs/sample1.json にある通り、次の様式です。  
```
{
    "connection_key": "response",
    "result": true,
    "redis_key": "0000000000000",
    "filepath": "/var/lib/aion/Data/direct-next-service_1/1634173065679.jpg",
    "status": "new",
    "age": 37.0,
    "gender": "male"
}
```  
#### Output1-2  
確証度を含めて取得する場合の出力データのJSONフォーマットは、outputs/sample2.json  にある通り、次の様式です。  
確証度が一定の閾値を超えているPersonIDが複数存在する場合、Personのレコードが複数になります。
```
{
    "connection_key": "response",
    "result": true,
    "redis_key": "0000000000000",
    "filepath": "/var/lib/aion/Data/direct-next-service_1/1634175178825.jpg",
    "person": {
        "additional_properties": {},
        "person_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "confidence": 0.94743
    },
    "guest_id": 1,
    "status": "existing"
}
```  

#### Output2
ログデータ(顔認証ログデータ解析用)のJSONフォーマットは、outputs/logs.sample.json にある通り、次の様式です。
```
{
    "imagePath": "/var/lib/aion/Data/direct-next-service_1/1634173065679.jpg",
    "faceId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "responseData": {
        "candidates": []
    }
}
```

## Getting Started
1. 下記コマンドでDockerイメージを作成します。  
```
make docker-build
```
2. aion-service-definitions/services.ymlに設定を記載し、AionCore経由でKubernetesコンテナを起動します。  
services.ymlへの記載例：    
```
azure-face-api-identifier-kube:
  startup: yes
  always: yes
  scale: 1
  env:
    MYSQL_USER: XXXXXXXX
    MYSQL_HOST: mysql
    MYSQL_PASSWORD: xxxxxxxxx
    MYSQL_DB: database
    RABBITMQ_URL: amqp://username:password@rabbitmq:5672/virtualhost
    QUEUE_ORIGIN: azure-face-api-identifier-kube-queue
    QUEUE_TO_FOR_LOG: send-data-to-azure-iot-hub-queue
```
## Flowchart
![フローチャート図](doc/omotebako_architecture_20211104.drawio.png)