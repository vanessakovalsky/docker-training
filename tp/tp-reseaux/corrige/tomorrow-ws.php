<?php
$host = getenv('TIME_WS_HOSTNAME');
$port = getenv('TIME_WS_PORT');
$c = curl_init( sprintf('http://%s:%s', $host, $port));
curl_setopt($c, CURLOPT_RETURNTRANSFER, 1);
$res = curl_exec($c);
printf(date("d/m/Y", $res+3600*24));