# azure-face-api-identifier-kube  
## 概要  
1枚の画像を Azure Face API(Detect) にかけ、返り値として、画像に映っているすべての人物の顔の位置座標(X軸/Y軸)、性別・年齢等の情報を取得します。  
Azure Face API の仕様により、顔の位置座標を形成する長方形の面積が最も広い顔が先頭に来ます。  
この仕様を利用して、その先頭の顔の FaceID、性別・年齢 等の 情報 を保持します。  
AzureのFaceAPIから顔IDを取得後、MySQLに保存された登録済みの顔IDと照らし合わせMySQLに存在すれば登録済み既存ユーザーと判定し、存在しなければ新規ユーザーと判定します。  

参考：Azure Face API の Person Group は、Azure Face API ユーザ のインスタンス毎に独立した顔情報の維持管理の単位です。  
参考：1枚の画像に対して複数人の顔が存在する場合は、１番確証度が大きい顔に対して判定を行います。  

## 前提条件  
* Azure Face API サービス に アクセスキー、エンドポイント、Person Group を登録します。登録されたエンドポイント、アクセスキー、Person Group を、本リポジトリ内の face-api-config.json に記載してください。  
* sample/test_01.jpgに任意の顔画像を配置してください。
* 登録されているエンドポイントを事前に学習させる。下記の手順で学習させることができます。  
```
# shellディレクトリ内のrecreate-group.shを実行する。シェル内のENDPOINT, SUBSCRIPTION_KEY, PERSON_GROUP_IDは使用するFaceAPIのエンドポイントに応じて書き換えて下さい。
$ bash recreate-group.sh
# 上記のコマンド実行するとPerson_idが出力されるので、train.shの３行目のPERSON_IDの値を置換しシェルを実行して下さい。
$ bash train.sh
```
* MySQLにface_id_azure (TEXT), guest_id (INT) カラムを持つguestテーブルを作成しておく。
* `shell/setup-env.sh`　は、face-api-config.jsonと.envを作成するためのシェルスクリプトです。PERSON_GROUP_ID、API_ACCESS_KEY、API_ENDPOINTに値を書き入れ、シェルスクリプトを実行してください。

## Requirements  
```
azure-cognitiveservices-vision-face==0.4.1
```
## I/O
RabbitMQのメッセージから下記の情報を入出力
#### Input
* 画像パス(image_path)
FaceAPIで判定したい画像のファイルパス
* ゲストキー(guest_key)
UIと判定結果を共有するためのRedisのキー
#### Output  
* ゲストキー(redis_key)
UIと判定結果を共有するためのRedisのキー。この後のマイクロサービスでUIと結果を共有するためにRedisのキーを出力します。
* 画像パス(filepath)
判定に仕様した画像パス。デバッグ用です。
* 顔ステータス(status)
MySQLに登録されている顔か出力する。値がnewの場合、新規。値がexistingの場合、MySQLに登録済みです。
* 人物オブジェクト配列 (person)
  マッチした人物候補のオブジェクトが最大5個まで格納される配列。デバッグ用です。
  * 人物ID（person_id）
  Azure側に登録されているゲストID
  * 確証度 (confidence)
  person_idの人物への一致の確からしさを0から1までの数値で表したもの
* 人物ID (guest_id)
MySQLに登録されているゲストIDを出力します。 


## Getting Started
1. 下記コマンドでDockerイメージを作成する。  
```
make docker-build
```
2. services.ymlに設定を記載し、AionCore経由でコンテナを起動する。  
services.ymlへの記載例  
multiple: noとして起動する。  
```
face-recognition-from-an-image:
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