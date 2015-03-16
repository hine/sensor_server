# sensor_server

RaspberryPiに接続したセンサーの情報をWebSocket経由でpushするセンサーサーバのテスト実装です。

## どうして作ったの？

CYBIRDのエンジニア社内LTイベントに呼んでいただいたので、そのネタに。

## 使用機材

* [RaspberryPi Model A+](http://www.raspberrypi.org/products/model-a-plus/)
* [3軸加速度(MPU-6050)センサーモジュール](http://www.aitendo.com/product/9549)

## サーバーサイド

サーバー側はTornadoを使い、Pythonで書いています。また、このセンサーはI2Cを用いるので、I2Cを有効にする必要があります。

## テストクライアント

簡易なテスト用のHTMLを用意しています。IPアドレス部分をRaspberryPiのIPアドレスに書き換えてください。
